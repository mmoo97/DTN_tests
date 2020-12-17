from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.safeio import formatted_print
from globus_cli.services.transfer import ENDPOINT_LIST_FIELDS, get_client


@command(
    "my-shared-endpoint-list",
    short_help="List all shared endpoints on an endpoint by the current user",
    adoc_examples="""[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint my-shared-endpoint-list $ep_id
----
""",
)
@endpoint_id_arg
def my_shared_endpoint_list(endpoint_id):
    """
    Show a list of all shared endpoints hosted on the target endpoint for which the user
    has the "administrator" or "access_manager" effective roles.
    """
    client = get_client()
    ep_iterator = client.my_shared_endpoint_list(endpoint_id)

    formatted_print(ep_iterator, fields=ENDPOINT_LIST_FIELDS)
