import click

from globus_cli.commands.bookmark.helpers import resolve_id_or_name
from globus_cli.parsing import command
from globus_cli.safeio import FORMAT_TEXT_RAW, formatted_print
from globus_cli.services.transfer import get_client


@command(
    "delete",
    adoc_output=(
        "When textual output is requested, the response contains a message "
        "indicating the success or failure of the operation."
    ),
    adoc_examples="""Delete a bookmark by name:

[source,bash]
----
$ globus bookmark delete "Bookmark Name"
----
""",
    short_help="Delete a bookmark",
)
@click.argument("bookmark_id_or_name")
def bookmark_delete(bookmark_id_or_name):
    """
    Delete one bookmark, given its ID or name.
    """
    client = get_client()
    bookmark_id = resolve_id_or_name(client, bookmark_id_or_name)["id"]

    res = client.delete_bookmark(bookmark_id)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
