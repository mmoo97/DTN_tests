from globus_cli.parsing import command, endpoint_id_arg, role_id_arg
from globus_cli.safeio import FORMAT_TEXT_RECORD, formatted_print
from globus_cli.services.auth import lookup_identity_name
from globus_cli.services.transfer import get_client


def lookup_principal(role):
    return lookup_identity_name(role["principal"])


@command(
    "show",
    short_help="Show full info for a role on an endpoint",
    adoc_output="""Textual output has the following fields:

- 'Principal Type'
- 'Principal'
- 'Role'

The principal is a user or group ID, and the principal type says which of these
types the principal is. The term "Principal" is used in the sense of "a
security principal", an entity which has some privileges associated with it.
""",
    adoc_examples="""Show detail for a specific role on an endpoint

[source,bash]
----
$ globus endpoint role show EP_ID ROLE_ID
----
""",
)
@endpoint_id_arg
@role_id_arg
def role_show(endpoint_id, role_id):
    """
    Show full info for a role on an endpoint.

    This does not show information about the permissions granted by a role; only what
    role a user or group has been granted, by name.

    You must have sufficient privileges to see the roles on the endpoint.
    """
    client = get_client()

    role = client.get_endpoint_role(endpoint_id, role_id)
    formatted_print(
        role,
        text_format=FORMAT_TEXT_RECORD,
        fields=(
            ("Principal Type", "principal_type"),
            ("Principal", lookup_principal),
            ("Role", "role"),
        ),
    )
