import webbrowser

import click

from globus_cli.config import (
    AUTH_AT_EXPIRES_OPTNAME,
    AUTH_AT_OPTNAME,
    AUTH_RT_OPTNAME,
    TRANSFER_AT_EXPIRES_OPTNAME,
    TRANSFER_AT_OPTNAME,
    TRANSFER_RT_OPTNAME,
    internal_auth_client,
    lookup_option,
    write_option,
)
from globus_cli.helpers.local_server import LocalServerError, start_local_server

SCOPES = (
    "openid profile email "
    "urn:globus:auth:scope:auth.globus.org:view_identity_set "
    "urn:globus:auth:scope:transfer.api.globus.org:all"
)


def do_link_auth_flow(session_params=None, force_new_client=False):
    """
    Prompts the user with a link to authenticate with globus auth
    and authorize the CLI to act on their behalf.
    """
    session_params = session_params or {}

    # get the ConfidentialApp client object
    auth_client = internal_auth_client(
        requires_instance=True, force_new_client=force_new_client
    )

    # start the Confidential App Grant flow
    auth_client.oauth2_start_flow(
        redirect_uri=auth_client.base_url + "v2/web/auth-code",
        refresh_tokens=True,
        requested_scopes=SCOPES,
    )

    # prompt
    additional_params = {"prompt": "login"}
    additional_params.update(session_params)
    linkprompt = "Please authenticate with Globus here"
    click.echo(
        "{0}:\n{1}\n{2}\n{1}\n".format(
            linkprompt,
            "-" * len(linkprompt),
            auth_client.oauth2_get_authorize_url(additional_params=additional_params),
        )
    )

    # come back with auth code
    auth_code = click.prompt("Enter the resulting Authorization Code here").strip()

    # finish auth flow
    exchange_code_and_store_config(auth_client, auth_code)
    return True


def do_local_server_auth_flow(session_params=None, force_new_client=False):
    """
    Starts a local http server, opens a browser to have the user authenticate,
    and gets the code redirected to the server (no copy and pasting required)
    """
    session_params = session_params or {}

    # start local server and create matching redirect_uri
    with start_local_server(listen=("127.0.0.1", 0)) as server:
        _, port = server.socket.getsockname()
        redirect_uri = "http://localhost:{}".format(port)

        # get the ConfidentialApp client object and start a flow
        auth_client = internal_auth_client(
            requires_instance=True, force_new_client=force_new_client
        )
        auth_client.oauth2_start_flow(
            refresh_tokens=True, redirect_uri=redirect_uri, requested_scopes=SCOPES
        )
        additional_params = {"prompt": "login"}
        additional_params.update(session_params)
        url = auth_client.oauth2_get_authorize_url(additional_params=additional_params)

        # open web-browser for user to log in, get auth code
        webbrowser.open(url, new=1)
        auth_code = server.wait_for_code()

    if isinstance(auth_code, LocalServerError):
        click.echo("Authorization failed: {}".format(auth_code), err=True)
        click.get_current_context().exit(1)
    elif isinstance(auth_code, Exception):
        click.echo(
            "Authorization failed with unexpected error:\n{}".format(auth_code),
            err=True,
        )
        click.get_current_context().exit(1)

    # finish auth flow and return true
    exchange_code_and_store_config(auth_client, auth_code)
    return True


def exchange_code_and_store_config(auth_client, auth_code):
    """
    Finishes auth flow after code is gotten from command line or local server.
    Exchanges code for tokens and gets user info from auth.
    Stores tokens and user info in config.
    """
    # do a token exchange with the given code
    tkn = auth_client.oauth2_exchange_code_for_tokens(auth_code)
    tkn = tkn.by_resource_server

    store_queue = []

    def _enqueue(optname, newval, revoke=True):
        store_queue.append((optname, newval, revoke))

    # extract access tokens from final response
    if "transfer.api.globus.org" in tkn:
        _enqueue(TRANSFER_RT_OPTNAME, tkn["transfer.api.globus.org"]["refresh_token"])
        _enqueue(TRANSFER_AT_OPTNAME, tkn["transfer.api.globus.org"]["access_token"])
        _enqueue(
            TRANSFER_AT_EXPIRES_OPTNAME,
            tkn["transfer.api.globus.org"]["expires_at_seconds"],
            revoke=False,
        )
    if "auth.globus.org" in tkn:
        _enqueue(AUTH_RT_OPTNAME, tkn["auth.globus.org"]["refresh_token"])
        _enqueue(AUTH_AT_OPTNAME, tkn["auth.globus.org"]["access_token"])
        _enqueue(
            AUTH_AT_EXPIRES_OPTNAME,
            tkn["auth.globus.org"]["expires_at_seconds"],
            revoke=False,
        )

    # revoke any existing tokens
    for optname in [optname for (optname, _val, revoke) in store_queue if revoke]:
        token = lookup_option(optname)
        if token:
            auth_client.oauth2_revoke_token(token)

    # write new data to config
    for optname, newval, _revoke in store_queue:
        write_option(optname, newval)
