import click
import globus_sdk
from globus_sdk.exc import AuthAPIError

from globus_cli.config import (
    AUTH_AT_EXPIRES_OPTNAME,
    AUTH_AT_OPTNAME,
    AUTH_RT_OPTNAME,
    CLIENT_ID_OPTNAME,
    CLIENT_SECRET_OPTNAME,
    TRANSFER_AT_EXPIRES_OPTNAME,
    TRANSFER_AT_OPTNAME,
    TRANSFER_RT_OPTNAME,
    internal_auth_client,
    internal_native_client,
    lookup_option,
    remove_option,
)
from globus_cli.parsing import command
from globus_cli.services.auth import get_auth_client

_RESCIND_HELP = """\
Rescinding Consents
-------------------
The logout command only revokes tokens that it can see in its storage.
If you are concerned that logout may have failed to revoke a token,
you may want to manually rescind the Globus CLI consent on the
Manage Consents Page:

    https://auth.globus.org/consents
"""


_LOGOUT_EPILOG = """\
You are now successfully logged out of the Globus CLI.
You may also want to logout of any browser session you have with Globus:

  https://auth.globus.org/v2/web/logout

Before attempting any further CLI commands, you will have to login again using

  globus login
"""


@command(
    "logout",
    short_help="Logout of the Globus CLI",
    disable_options=["format", "map_http_status"],
)
@click.confirmation_option(
    prompt="Are you sure you want to logout?",
    help='Automatically say "yes" to all prompts',
)
def logout_command():
    """
    Logout of the Globus CLI

    This command both removes all tokens used for authenticating the user from local
    storage and revokes them so that they cannot be used anymore globally.

    If an expected token cannot be found in local storage a warning will be raised
    as it is possible the token still exists and needs to be manually rescinded
    at https://auth.globus.org/consents for security.
    """
    # try to get the user's preferred username from userinfo
    # if an API error is raised, they probably are not logged in
    try:
        username = get_auth_client().oauth2_userinfo()["preferred_username"]
    except AuthAPIError:
        click.echo(
            (
                "Unable to lookup username. You may not be logged in. "
                "Attempting logout anyway...\n"
            )
        )
        username = None
    click.echo(
        u"Logging out of Globus{}\n".format(u" as " + username if username else "")
    )

    # we use a Native Client to prevent an invalid instance client
    # from preventing token revocation
    native_client = internal_native_client()

    # remove tokens from config and revoke them
    # also, track whether or not we should print the rescind help
    print_rescind_help = False
    for token_opt in (
        TRANSFER_RT_OPTNAME,
        TRANSFER_AT_OPTNAME,
        AUTH_RT_OPTNAME,
        AUTH_AT_OPTNAME,
    ):
        # first lookup the token -- if not found we'll continue
        token = lookup_option(token_opt)
        if not token:
            click.echo(
                (
                    'Warning: Found no token named "{}"! '
                    "Recommend rescinding consent"
                ).format(token_opt)
            )
            print_rescind_help = True
            continue
        # token was found, so try to revoke it
        try:
            native_client.oauth2_revoke_token(token)
        # if we network error, revocation failed -- print message and abort so
        # that we can revoke later when the network is working
        except globus_sdk.NetworkError:
            click.echo(
                (
                    "Failed to reach Globus to revoke tokens. "
                    "Because we cannot revoke these tokens, cancelling "
                    "logout"
                )
            )
            click.get_current_context().exit(1)
        # finally, we revoked, so it's safe to remove the token
        remove_option(token_opt)

    # delete the instance client if one exists
    client_id = lookup_option(CLIENT_ID_OPTNAME)

    if client_id:
        instance_client = internal_auth_client()
        try:
            instance_client.delete("/v2/api/clients/{}".format(client_id))

        # if the client secret has been invalidated or the client has
        # already been removed, we continue on
        except AuthAPIError:
            pass

    # remove deleted client values and expiration times
    for opt in (
        CLIENT_ID_OPTNAME,
        CLIENT_SECRET_OPTNAME,
        TRANSFER_AT_EXPIRES_OPTNAME,
        AUTH_AT_EXPIRES_OPTNAME,
    ):
        remove_option(opt)

    # if print_rescind_help is true, we printed warnings above
    # so, jam out an extra newline as a separator
    click.echo(("\n" if print_rescind_help else "") + _LOGOUT_EPILOG)

    # if some token wasn't found in the config, it means its possible that the
    # config file was removed without logout
    # in that case, the user should rescind the CLI consent to invalidate any
    # potentially leaked refresh tokens, so print the help on that
    if print_rescind_help:
        click.echo(_RESCIND_HELP)
