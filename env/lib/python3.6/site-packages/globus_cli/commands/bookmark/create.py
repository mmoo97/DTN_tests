import click

from globus_cli.parsing import ENDPOINT_PLUS_REQPATH, command
from globus_cli.safeio import formatted_print
from globus_cli.services.transfer import get_client


@command(
    "create",
    adoc_output=(
        "When textual output is requested, the only result shown is the ID of the"
        "created bookmark."
    ),
    adoc_examples=r"""Create a bookmark named 'mybookmark':

[source,bash]
----
$ globus bookmark create 'ddb59aef-6d04-11e5-ba46-22000b92c6ec:/~/' mybookmark
----

Take a specific field from the JSON output and format it into unix-friendly
output by using '--jmespath' and '--format=UNIX':

[source,bash]
----
$ globus bookmark create \
    'ddb59aef-6d04-11e5-ba46-22000b92c6ec:/~/' mybookmark \
     -F unix --jmespath 'id'
----
""",
    short_help="Create a bookmark for the current user",
)
@click.argument("endpoint_plus_path", type=ENDPOINT_PLUS_REQPATH)
@click.argument("bookmark_name")
def bookmark_create(endpoint_plus_path, bookmark_name):
    """
    Create a new bookmark. Given an endpoint plus a path, and a name for the bookmark,
    the service will generate the bookmark's ID.

    Bookmarks are aliases for locations on endpoints, and their names are unique
    per account. You may not have multiple bookmarks with the same name. You can
    use bookmarks in other commands by using *globus bookmark show*.

    The new bookmark name may be up to 128 characters long.
    Bookmarks are only visible and usable for the user who created them.  If the
    target endpoint is private or deleted, the bookmark is unusable.

    'PATH' is assumed to be URL-encoded.  'PATH' must be a directory and end with "/".
    """
    endpoint_id, path = endpoint_plus_path
    client = get_client()

    submit_data = {"endpoint_id": str(endpoint_id), "path": path, "name": bookmark_name}

    res = client.create_bookmark(submit_data)
    formatted_print(res, simple_text="Bookmark ID: {}".format(res["id"]))
