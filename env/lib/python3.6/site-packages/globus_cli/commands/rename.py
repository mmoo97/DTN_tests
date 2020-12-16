import click

from globus_cli.parsing import ENDPOINT_PLUS_REQPATH, command
from globus_cli.safeio import FORMAT_TEXT_RAW, formatted_print
from globus_cli.services.transfer import autoactivate, get_client


@command(
    "rename",
    short_help="Rename a file or directory on an endpoint",
    adoc_examples="""Rename a directory:

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus rename $ep_id:~/tempdir $ep_id:~/project-foo
----
""",
)
@click.argument("source", metavar="ENDPOINT_ID:SOURCE_PATH", type=ENDPOINT_PLUS_REQPATH)
@click.argument(
    "destination", metavar="ENDPOINT_ID:DEST_PATH", type=ENDPOINT_PLUS_REQPATH
)
def rename_command(source, destination):
    """Rename a file or directory on an endpoint.

    The old path must be an existing file or directory. The new path must not yet
    exist.

    The new path does not have to be in the same directory as the old path, but
    most endpoints will require it to stay on the same filesystem.

    The endpoint must be entered twice for the sake of path syntax consistency.
    """
    source_ep, source_path = source
    dest_ep, dest_path = destination

    if source_ep != dest_ep:
        raise click.UsageError(
            (
                "rename requires that the source and dest "
                "endpoints are the same, {} != {}"
            ).format(source_ep, dest_ep)
        )
    endpoint_id = source_ep

    client = get_client()
    autoactivate(client, endpoint_id, if_expires_in=60)

    res = client.operation_rename(endpoint_id, oldpath=source_path, newpath=dest_path)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
