from globus_sdk import TransferAPIError

from globus_cli.parsing import command
from globus_cli.safeio import formatted_print
from globus_cli.services.transfer import (
    display_name_or_cname,
    get_client,
    iterable_response_to_dict,
)


@command(
    "list",
    adoc_output="""When textual output is requested, the following fields are displayed:
- 'Name'
- 'Bookmark ID'
- 'Endpoint ID'
- 'Endpoint Name'
- 'Path'
""",
    adoc_examples="""
[source,bash]
----
$ globus bookmark list
----

Format specific fields in the bookmark list into unix-friendly columnar
output:

[source,bash]
----
$ globus bookmark list --jmespath='DATA[*].[name, endpoint_id]' --format=unix
----
""",
    short_help="List your bookmarks",
)
def bookmark_list():
    """List all bookmarks for the current user"""
    client = get_client()

    bookmark_iterator = client.bookmark_list()

    def get_ep_name(item):
        ep_id = item["endpoint_id"]
        try:
            ep_doc = client.get_endpoint(ep_id)
            return display_name_or_cname(ep_doc)
        except TransferAPIError as err:
            if err.code == "EndpointDeleted":
                return "[DELETED ENDPOINT]"
            else:
                raise err

    formatted_print(
        bookmark_iterator,
        fields=[
            ("Name", "name"),
            ("Bookmark ID", "id"),
            ("Endpoint ID", "endpoint_id"),
            ("Endpoint Name", get_ep_name),
            ("Path", "path"),
        ],
        response_key="DATA",
        json_converter=iterable_response_to_dict,
    )
