import click

from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.safeio import FORMAT_TEXT_RAW, formatted_print
from globus_cli.services.transfer import get_client


@command(
    "delete",
    short_help="Delete an access control rule",
    adoc_examples="""[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ rule_id=1ddeddda-1ae8-11e7-bbe4-22000b9a448b
$ globus endpoint permission delete $ep_id $rule_id
----
""",
)
@endpoint_id_arg
@click.argument("rule_id")
def delete_command(endpoint_id, rule_id):
    """
    Delete an existing access control rule, removing whatever permissions it previously
    granted users on the endpoint.

    Note you cannot remove the built in rule that gives the endpoint owner full
    read and write access to the endpoint.
    """
    client = get_client()

    res = client.delete_endpoint_acl_rule(endpoint_id, rule_id)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
