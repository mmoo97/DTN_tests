import click

from globus_cli.commands.bookmark.helpers import resolve_id_or_name
from globus_cli.parsing import command
from globus_cli.safeio import FORMAT_TEXT_RECORD, formatted_print, is_verbose
from globus_cli.services.transfer import get_client


@command(
    "show",
    adoc_output="""
When textual output is requested, the output varies depending on verbosity.

By default, output is simply 'ENDPOINT_ID:PATH'

If *-v* or *--verbose* is given, output has the following fields:

- 'ID'
- 'Name'
- 'Endpoint ID'
- 'Path'
""",
    adoc_examples="""Resolve a bookmark, for use in another command:

[source,bash]
----
$ globus ls "$(globus bookmark show BOOKMARK_NAME)"
----
""",
    short_help="Resolve a bookmark name or ID to an endpoint:path",
)
@click.argument("bookmark_id_or_name")
def bookmark_show(bookmark_id_or_name):
    """
    Given a single bookmark ID or bookmark name, show the bookmark details. By default,
    when the format is TEXT, this will display the endpoint ID and path in
    'ENDPOINT_ID:PATH' notation.

    The default output is suitable for use in a subshell in another command.

    If *-v, --verbose* is given, several fields will be displayed.
    """
    client = get_client()
    res = resolve_id_or_name(client, bookmark_id_or_name)
    formatted_print(
        res,
        text_format=FORMAT_TEXT_RECORD,
        fields=(
            ("ID", "id"),
            ("Name", "name"),
            ("Endpoint ID", "endpoint_id"),
            ("Path", "path"),
        ),
        simple_text=(
            # standard output is endpoint:path format
            "{}:{}".format(res["endpoint_id"], res["path"])
            # verbose output includes all fields
            if not is_verbose()
            else None
        ),
    )
