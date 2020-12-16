import click

from globus_cli.helpers import (
    do_link_auth_flow,
    do_local_server_auth_flow,
    is_remote_session,
)
from globus_cli.parsing import command, no_local_server_option


@command(
    "consent",
    short_help="Update your session with specific consents",
    disable_options=["format", "map_http_status"],
)
@no_local_server_option
@click.argument("SCOPES", nargs=-1, required=True)
def session_consent(scopes, no_local_server):
    """
    Update your current CLI auth session by authenticating with a specific scope or set
    of scopes.

    This command is necessary when the CLI needs access to resources which require the
    user to explicitly consent to access.
    """
    session_params = {"scope": " ".join(scopes)}

    # use a link login if remote session or user requested
    if no_local_server or is_remote_session():
        do_link_auth_flow(session_params=session_params)

    # otherwise default to a local server login flow
    else:
        click.echo(
            "You are running 'globus session consent', "
            "which should automatically open a browser window for you to "
            "authenticate with specific identities.\n"
            "If this fails or you experience difficulty, try "
            "'globus session consent --no-local-server'"
            "\n---"
        )
        do_local_server_auth_flow(session_params=session_params)

    click.echo("\nYou have successfully updated your CLI session.\n")
