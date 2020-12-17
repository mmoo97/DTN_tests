import random
import sys
import time
import uuid
from textwrap import dedent

import click
from globus_sdk import RefreshTokenAuthorizer, TransferClient
from globus_sdk.base import safe_stringify
from globus_sdk.exc import NetworkError

from globus_cli import version
from globus_cli.config import (
    get_transfer_tokens,
    internal_auth_client,
    set_transfer_tokens,
)
from globus_cli.parsing import EXPLICIT_NULL
from globus_cli.safeio import FORMAT_SILENT, formatted_print
from globus_cli.services.recursive_ls import RecursiveLsResponse


class RetryingTransferClient(TransferClient):
    """
    Wrapper around TransferClient that retries safe resources on NetworkErrors
    """

    def __init__(self, tries=10, *args, **kwargs):
        super(RetryingTransferClient, self).__init__(*args, **kwargs)
        self.tries = tries

    def retry(self, f, *args, **kwargs):
        """
        Retries the given function self.tries times on NetworkErros
        """
        backoff = random.random() / 100  # 5ms on average
        for _ in range(self.tries - 1):
            try:
                return f(*args, **kwargs)
            except NetworkError:
                time.sleep(backoff)
                backoff *= 2
        return f(*args, **kwargs)

    # get and put should always be safe to retry
    def get(self, *args, **kwargs):
        return self.retry(super(RetryingTransferClient, self).get, *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.retry(super(RetryingTransferClient, self).put, *args, **kwargs)

    # task submission is safe, as the data contains a unique submission-id
    def submit_transfer(self, *args, **kwargs):
        return self.retry(
            super(RetryingTransferClient, self).submit_transfer, *args, **kwargs
        )

    def submit_delete(self, *args, **kwargs):
        return self.retry(
            super(RetryingTransferClient, self).submit_delete, *args, **kwargs
        )

    # TDOD: Remove this function when endpoints natively support recursive ls
    def recursive_operation_ls(
        self, endpoint_id, depth=3, filter_after_first=True, **params
    ):
        """
        Makes recursive calls to ``GET /operation/endpoint/<endpoint_id>/ls``
        Does not preserve access to top level operation_ls fields, but
        adds a "path" field for every item that represents the full
        path to that item.
        :rtype: iterable of :class:`GlobusResponse
                <globus_sdk.response.GlobusResponse>`
        **Parameters**
            ``endpoint_id`` (*string*)
              The endpoint being recursively ls'ed. If no "path" is given in
              params, the start path is determined by this endpoint.
            ``depth`` (*int*)
              The maximum file depth the recursive ls will go to.
            ``filter_after_first`` (*bool*)
              If False, any "filter" in params will only be applied to the
              first, top level ls, all results beyond that will be unfiltered.
            ``params``
              Parameters that will be passed through as query params.
        **Examples**
        >>> tc = globus_sdk.TransferClient(...)
        >>> for entry in tc.recursive_operation_ls(ep_id, path="/~/project1/"):
        >>>     print(entry["path"], entry["type"])
        **External Documentation**
        See
        `List Directory Contents \
        <https://docs.globus.org/api/transfer/file_operations/#list_directory_contents>`_
        in the REST documentation for details, but note that top level data
        fields are no longer available and an additional per item
        "path" field is added.
        """
        endpoint_id = safe_stringify(endpoint_id)
        self.logger.info(
            "TransferClient.recursive_operation_ls({}, {}, {})".format(
                endpoint_id, depth, params
            )
        )
        return RecursiveLsResponse(self, endpoint_id, depth, filter_after_first, params)


def _update_tokens(token_response):
    tokens = token_response.by_resource_server["transfer.api.globus.org"]
    set_transfer_tokens(
        tokens["access_token"], tokens["refresh_token"], tokens["expires_at_seconds"]
    )


def get_client():
    tokens = get_transfer_tokens()
    authorizer = None

    # if there's a refresh token, use it to build the authorizer
    if tokens["refresh_token"] is not None:
        authorizer = RefreshTokenAuthorizer(
            tokens["refresh_token"],
            internal_auth_client(),
            tokens["access_token"],
            tokens["access_token_expires"],
            on_refresh=_update_tokens,
        )

    return RetryingTransferClient(
        tries=10, authorizer=authorizer, app_name=version.app_name
    )


def display_name_or_cname(ep_doc):
    return ep_doc["display_name"] or ep_doc["canonical_name"]


def iterable_response_to_dict(iterator):
    output_dict = {"DATA": []}
    for item in iterator:
        dat = item
        try:
            dat = item.data
        except AttributeError:
            pass
        output_dict["DATA"].append(dat)
    return output_dict


def assemble_generic_doc(datatype, **kwargs):
    doc = {"DATA_TYPE": datatype}
    for key, val in kwargs.items():
        if isinstance(val, uuid.UUID):
            val = str(val)

        if val == EXPLICIT_NULL:
            doc[key] = None
        elif val is not None:
            doc[key] = val
    return doc


def supported_activation_methods(res):
    """
    Given an activation_requirements document
    returns a list of activation methods supported by this endpoint.
    """
    supported = ["web"]  # web activation is always supported.

    # oauth
    if res["oauth_server"]:
        supported.append("oauth")

    for req in res["DATA"]:
        # myproxy
        if (
            req["type"] == "myproxy"
            and req["name"] == "hostname"
            and req["value"] != "myproxy.globusonline.org"
        ):
            supported.append("myproxy")

        # delegate_proxy
        if req["type"] == "delegate_proxy" and req["name"] == "public_key":
            supported.append("delegate_proxy")

    return supported


def activation_requirements_help_text(res, ep_id):
    """
    Given an activation requirements document and an endpoint_id
    returns a string of help text for how to activate the endpoint
    """
    methods = supported_activation_methods(res)

    lines = [
        "This endpoint supports the following activation methods: ",
        ", ".join(methods).replace("_", " "),
        "\n",
        (
            "For web activation use:\n"
            "'globus endpoint activate --web {}'\n".format(ep_id)
            if "web" in methods
            else ""
        ),
        (
            "For myproxy activation use:\n"
            "'globus endpoint activate --myproxy {}'\n".format(ep_id)
            if "myproxy" in methods
            else ""
        ),
        (
            "For oauth activation use web activation:\n"
            "'globus endpoint activate --web {}'\n".format(ep_id)
            if "oauth" in methods
            else ""
        ),
        (
            "For delegate proxy activation use:\n"
            "'globus endpoint activate --delegate-proxy "
            "X.509_PEM_FILE {}'\n".format(ep_id)
            if "delegate_proxy" in methods
            else ""
        ),
        (
            "Delegate proxy activation requires an additional dependency on "
            "cryptography. See the docs for details:\n"
            "https://docs.globus.org/cli/reference/endpoint_activate/\n"
            if "delegate_proxy" in methods
            else ""
        ),
    ]

    return "".join(lines)


def autoactivate(client, endpoint_id, if_expires_in=None):
    """
    Attempts to auto-activate the given endpoint with the given client
    If auto-activation fails, parses the returned activation requirements
    to determine which methods of activation are supported, then tells
    the user to use 'globus endpoint activate' with the correct options(s)
    """
    kwargs = {}
    if if_expires_in is not None:
        kwargs["if_expires_in"] = if_expires_in

    res = client.endpoint_autoactivate(endpoint_id, **kwargs)
    if res["code"] == "AutoActivationFailed":

        message = (
            "The endpoint could not be auto-activated and must be "
            "activated before it can be used.\n\n"
            + activation_requirements_help_text(res, endpoint_id)
        )

        click.echo(message, err=True)
        click.get_current_context().exit(1)

    else:
        return res


def get_endpoint_w_server_list(endpoint_id):
    """
    A helper for handling endpoint server list lookups correctly accounting
    for various endpoint types.

    - Raises click.UsageError when used on Shares
    - Returns (<get_endpoint_response>, "S3") for S3 endpoints
    - Returns (<get_endpoint_response>, <server_list_response>) for all other
      Endpoints
    """
    client = get_client()

    endpoint = client.get_endpoint(endpoint_id)

    if endpoint["host_endpoint_id"]:  # not GCS -- this is a share endpoint
        raise click.UsageError(
            dedent(
                u"""\
            {id} ({0}) is a share and does not have servers.

            To see details of the share, use
                globus endpoint show {id}

            To list the servers on the share's host endpoint, use
                globus endpoint server list {host_endpoint_id}
        """
            ).format(display_name_or_cname(endpoint), **endpoint.data)
        )

    if endpoint["s3_url"]:  # not GCS -- legacy S3 endpoint type
        return (endpoint, "S3")

    else:
        return (endpoint, client.endpoint_server_list(endpoint_id))


def task_wait_with_io(
    meow, heartbeat, polling_interval, timeout, task_id, timeout_exit_code, client=None
):
    """
    Options are the core "task wait" options, including the `--meow` easter
    egg.

    This does the core "task wait" loop, including all of the IO.
    It *does exit* on behalf of the caller. (We can enhance with a
    `noabort=True` param or somesuch in the future if necessary.)
    """
    client = client or get_client()

    def timed_out(waited_time):
        if timeout is None:
            return False
        else:
            return waited_time >= timeout

    def check_completed():
        completed = client.task_wait(
            task_id, timeout=polling_interval, polling_interval=polling_interval
        )
        if completed:
            if heartbeat:
                click.echo("", err=True)
            # meowing tasks wake up!
            if meow:
                click.echo(
                    r"""
                  _..
  /}_{\           /.-'
 ( a a )-.___...-'/
 ==._.==         ;
      \ i _..._ /,
      {_;/   {_//""",
                    err=True,
                )

            # TODO: possibly update TransferClient.task_wait so that we don't
            # need to do an extra fetch to get the task status after completion
            res = client.get_task(task_id)
            formatted_print(res, text_format=FORMAT_SILENT)

            status = res["status"]
            if status == "SUCCEEDED":
                click.get_current_context().exit(0)
            else:
                click.get_current_context().exit(1)

        return completed

    # Tasks start out sleepy
    if meow:
        click.echo(
            r"""
   |\      _,,,---,,_
   /,`.-'`'    -.  ;-;;,_
  |,4-  ) )-,_..;\ (  `'-'
 '---''(_/--'  `-'\_)""",
            err=True,
        )

    waited_time = 0
    while not timed_out(waited_time) and not check_completed():
        if heartbeat:
            click.echo(".", err=True, nl=False)
            sys.stderr.flush()

        waited_time += polling_interval

    # add a trailing newline to heartbeats if we fail
    if heartbeat:
        click.echo("", err=True)

    exit_code = 1
    if timed_out(waited_time):
        click.echo(
            "Task has yet to complete after {} seconds".format(timeout), err=True
        )
        exit_code = timeout_exit_code

    # output json if requested, but nothing for text mode
    res = client.get_task(task_id)
    formatted_print(res, text_format=FORMAT_SILENT)

    click.get_current_context().exit(exit_code)


ENDPOINT_LIST_FIELDS = (
    ("ID", "id"),
    ("Owner", "owner_string"),
    ("Display Name", display_name_or_cname),
)
