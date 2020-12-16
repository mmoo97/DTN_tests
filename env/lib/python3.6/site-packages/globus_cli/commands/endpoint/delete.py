from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.safeio import FORMAT_TEXT_RAW, formatted_print
from globus_cli.services.transfer import get_client


@command(
    "delete",
    short_help="Delete an endpoint",
    adoc_examples="""[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint delete $ep_id
----
""",
)
@endpoint_id_arg
def endpoint_delete(endpoint_id):
    """Delete a given endpoint.

    WARNING: Deleting an endpoint will permanently disable any existing shared
    endpoints that are hosted on it.
    """
    client = get_client()
    res = client.delete_endpoint(endpoint_id)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
