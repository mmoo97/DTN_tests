from globus_sdk import IdentityMap

from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.safeio import formatted_print
from globus_cli.services.auth import get_auth_client
from globus_cli.services.transfer import get_client


@command(
    "list",
    short_help="List access control rules",
    adoc_examples="""[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint permission list $ep_id
----
""",
)
@endpoint_id_arg
def list_command(endpoint_id):
    """List all rules in an endpoint's access control list."""
    client = get_client()

    rules = client.endpoint_acl_list(endpoint_id)

    resolved_ids = IdentityMap(
        get_auth_client(),
        (x["principal"] for x in rules if x["principal_type"] == "identity"),
    )

    def principal_str(rule):
        principal = rule["principal"]
        if rule["principal_type"] == "identity":
            try:
                return resolved_ids[principal]["username"]
            except KeyError:
                return principal
        if rule["principal_type"] == "group":
            return (u"https://app.globus.org/groups/{}").format(principal)
        return rule["principal_type"]

    formatted_print(
        rules,
        fields=[
            ("Rule ID", "id"),
            ("Permissions", "permissions"),
            ("Shared With", principal_str),
            ("Path", "path"),
        ],
    )
