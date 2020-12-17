import base64
import uuid

import click
from globus_sdk import GlobusResponse

from globus_cli.parsing import command
from globus_cli.safeio import FORMAT_TEXT_TABLE, formatted_print, is_verbose
from globus_cli.services.auth import get_auth_client


@command("get-groups", short_help="Lookup Globus Groups")
@click.argument("values", required=True, nargs=-1)
def get_identities_command(identities):
    """
    Lookup Globus Groups given one or more globus identities.
    """
    client = get_auth_client()

    resolved_values = [_try_b32_decode(v) or v for v in values]

    # since API doesn't accept mixed ids and usernames,
    # split input values into separate lists
    ids = []
    usernames = []
    for val in resolved_values:
        try:
            uuid.UUID(val)
            ids.append(val)
        except ValueError:
            usernames.append(val)

    # make two calls to get_identities with ids and usernames
    # then combine the calls into one response
    results = []
    if len(ids):
        results += client.get_identities(ids=ids, provision=provision)["identities"]
    if len(usernames):
        results += client.get_identities(usernames=usernames, provision=provision)[
            "identities"
        ]
    res = GlobusResponse({"identities": results})

    def _custom_text_format(identities):
        """
        Non-verbose text output is customized
        """

        def resolve_identity(value):
            """
            helper to deal with variable inputs and uncertain response order
            """
            for identity in identities:
                if identity["id"] == value:
                    return identity["username"]
                if identity["username"] == value:
                    return identity["id"]
            return "NO_SUCH_IDENTITY"

        # standard output is one resolved identity per line in the same order
        # as the inputs. A resolved identity is either a username if given a
        # UUID vice versa, or "NO_SUCH_IDENTITY" if the identity could not be
        # found
        for val in resolved_values:
            click.echo(resolve_identity(val))

    formatted_print(
        res,
        response_key="identities",
        fields=[
            ("ID", "id"),
            ("Username", "username"),
            ("Full Name", "name"),
            ("Organization", "organization"),
            ("Email Address", "email"),
        ],
        # verbose output is a table. Order not guaranteed, may contain
        # duplicates
        text_format=(FORMAT_TEXT_TABLE if is_verbose() else _custom_text_format),
    )
