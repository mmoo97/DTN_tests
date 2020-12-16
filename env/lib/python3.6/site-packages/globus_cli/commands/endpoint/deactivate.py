from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.safeio import FORMAT_TEXT_RAW, formatted_print
from globus_cli.services.transfer import get_client


@command(
    "deactivate",
    short_help="Deactivate an endpoint",
    adoc_examples="""Deactivate an endpoint:

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint deactivate $ep_id
----
""",
)
@endpoint_id_arg
def endpoint_deactivate(endpoint_id):
    """
    Remove the credential previously assigned to an endpoint via
    'globus endpoint activate' or any other form of endpoint activation
    """
    client = get_client()
    res = client.endpoint_deactivate(endpoint_id)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
