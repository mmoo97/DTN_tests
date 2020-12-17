import click

from globus_cli.parsing import (
    ENDPOINT_PLUS_REQPATH,
    command,
    endpoint_create_and_update_params,
    one_use_option,
    validate_endpoint_create_and_update_params,
)
from globus_cli.safeio import FORMAT_TEXT_RECORD, formatted_print
from globus_cli.services.transfer import assemble_generic_doc, autoactivate, get_client

COMMON_FIELDS = [("Message", "message"), ("Endpoint ID", "id")]

GCP_FIELDS = [("Setup Key", "globus_connect_setup_key")]


@command(
    "create",
    short_help="Create a new endpoint",
    adoc_examples="""Create a Globus Connect Personal endpoint:

[source,bash]
----
$ globus endpoint create --personal my_gcp_endpoint
----

Create a Globus Connect Server endpoint:

[source,bash]
----
$ globus endpoint create --server my_gcs_endpoint
----

Create a shared endpoint hosted on another endpoint:

[source,bash]
----
$ host_ep=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint create --shared host_ep:~/ my_shared_endpoint
----
""",
)
@endpoint_create_and_update_params(create=True)
@one_use_option(
    "--personal",
    is_flag=True,
    help=(
        "Create a Globus Connect Personal endpoint. "
        "Mutually exclusive with --server and --shared. "
    ),
)
@one_use_option(
    "--server",
    is_flag=True,
    help=(
        "Create a Globus Connect Server endpoint. "
        "Mutually exclusive with --personal and --shared."
    ),
)
@one_use_option(
    "--shared",
    default=None,
    type=ENDPOINT_PLUS_REQPATH,
    help=(
        "Create a shared endpoint hosted on the given endpoint "
        "and path. Mutually exclusive with --personal and "
        "--server."
    ),
)
def endpoint_create(**kwargs):
    """
    Create a new endpoint.

    Requires a display name and exactly one of --personal, --server, or --shared to make
    a Globus Connect Personal, Globus Connect Server, or Shared endpoint respectively.
    """
    client = get_client()

    # get endpoint type, ensure unambiguous.
    personal = kwargs.pop("personal")
    server = kwargs.pop("server")
    shared = kwargs.pop("shared")

    if personal and (not server) and (not shared):
        endpoint_type = "personal"
    elif server and (not personal) and (not shared):
        endpoint_type = "server"
    elif shared and (not personal) and (not server):
        endpoint_type = "shared"
    else:
        raise click.UsageError(
            "Exactly one of --personal, --server, or --shared is required."
        )

    # validate options
    kwargs["is_globus_connect"] = personal or None
    validate_endpoint_create_and_update_params(endpoint_type, False, kwargs)

    # shared endpoint creation
    if shared:
        endpoint_id, host_path = shared
        kwargs["host_endpoint"] = endpoint_id
        kwargs["host_path"] = host_path

        ep_doc = assemble_generic_doc("shared_endpoint", **kwargs)
        autoactivate(client, endpoint_id, if_expires_in=60)
        res = client.create_shared_endpoint(ep_doc)

    # non shared endpoint creation
    else:
        # omit `is_globus_connect` key if not GCP, otherwise include as `True`
        ep_doc = assemble_generic_doc("endpoint", **kwargs)
        res = client.create_endpoint(ep_doc)

    # output
    formatted_print(
        res,
        fields=(COMMON_FIELDS + GCP_FIELDS if personal else COMMON_FIELDS),
        text_format=FORMAT_TEXT_RECORD,
    )
