import time

import globus_sdk

from globus_cli.config import AUTH_AT_OPTNAME, internal_auth_client, lookup_option
from globus_cli.parsing import command
from globus_cli.safeio import formatted_print, print_command_hint
from globus_cli.services.auth import get_auth_client


@command(
    "show",
    short_help="Show your current CLI auth session",
    adoc_output="""Note: this output will not show your primary identity if it is not
in session. For information on your identity set use 'globus whoami'.

When textual output is requested, the output will be a table with
the following fields:

- 'Username'
- 'ID'
- 'Auth Time'

When JSON output is requested the output will also have the session id
if needed.
""",
    adoc_examples="""Display the current session with JSON output

[source,bash]
----
$ globus session show --format json
----
""",
)
def session_show():
    """List all identities in your current CLI auth session.

    Lists identities that are in the session tied to the CLI's access tokens along with
    the time the user authenticated with that identity.
    """
    # get a token to introspect, refreshing if neccecary
    auth_client = internal_auth_client()
    try:
        auth_client.authorizer._check_expiration_time()
    except AttributeError:  # if we have no RefreshTokenAuthorizor
        pass
    access_token = lookup_option(AUTH_AT_OPTNAME)

    # only instance clients can introspect tokens
    if isinstance(auth_client, globus_sdk.ConfidentialAppAuthClient):
        res = auth_client.oauth2_token_introspect(access_token, include="session_info")

        session_info = res.get("session_info", {})
        authentications = session_info.get("authentications") or {}

    # empty session if still using Native App Client
    else:
        session_info = {}
        authentications = {}

    # resolve ids to human readable usernames
    resolved_ids = globus_sdk.IdentityMap(get_auth_client(), list(authentications))

    # put the nested dicts in a format table output can work with
    # while also converting vals into human readable formats
    list_data = [
        {
            "id": key,
            "username": resolved_ids.get(key, {}).get("username"),
            "auth_time": time.strftime(
                "%Y-%m-%d %H:%M %Z", time.localtime(vals["auth_time"])
            ),
        }
        for key, vals in authentications.items()
    ]

    print_command_hint(
        "For information on your primary identity or full identity set see\n"
        "  globus whoami\n"
    )

    formatted_print(
        list_data,
        json_converter=lambda x: session_info,
        fields=[("Username", "username"), ("ID", "id"), ("Auth Time", "auth_time")],
    )
