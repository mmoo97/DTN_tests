import click

from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.safeio import FORMAT_TEXT_RAW, formatted_print
from globus_cli.services.transfer import assemble_generic_doc, get_client


@command(
    "update",
    short_help="Update an access control rule",
    adoc_examples="""Change existing access control rule to read only:

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ rule_id=1ddeddda-1ae8-11e7-bbe4-22000b9a448b
$ globus endpoint permission update $ep_id $rule_id --permissions r
----
""",
)
@endpoint_id_arg
@click.argument("rule_id")
@click.option(
    "--permissions",
    required=True,
    type=click.Choice(("r", "rw"), case_sensitive=False),
    help="Permissions to add. Read-Only or Read/Write",
)
def update_command(permissions, rule_id, endpoint_id):
    """
    Update an existing access control rule's permissions.

    The --permissions option is required, as it is currently the only field
    that can be updated.
    """
    client = get_client()

    rule_data = assemble_generic_doc("access", permissions=permissions)
    res = client.update_endpoint_acl_rule(endpoint_id, rule_id, rule_data)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
