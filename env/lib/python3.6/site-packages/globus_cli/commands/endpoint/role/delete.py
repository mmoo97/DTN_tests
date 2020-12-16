from globus_cli.parsing import command, endpoint_id_arg, role_id_arg
from globus_cli.safeio import FORMAT_TEXT_RAW, formatted_print
from globus_cli.services.transfer import get_client


@command(
    "delete",
    short_help="Remove a role from an endpoint",
    adoc_output="Textual output is a simple success message in the absence of errors.",
    adoc_examples="""Delete role '0f007eec-1aeb-11e7-aec4-3c970e0c9cc4' on endpoint
'ddb59aef-6d04-11e5-ba46-22000b92c6ec':

[source,bash]
----
$ globus endpoint role delete 'ddb59aef-6d04-11e5-ba46-22000b92c6ec' \
    '0f007eec-1aeb-11e7-aec4-3c970e0c9cc4'
----
""",
)
@endpoint_id_arg
@role_id_arg
def role_delete(role_id, endpoint_id):
    """
    Remove a role from an endpoint.

    You must have sufficient privileges to modify the roles on the endpoint.
    """
    client = get_client()
    res = client.delete_endpoint_role(endpoint_id, role_id)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
