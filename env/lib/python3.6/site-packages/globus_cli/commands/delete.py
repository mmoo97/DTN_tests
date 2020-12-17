import click
from globus_sdk import DeleteData

from globus_cli.parsing import (
    ENDPOINT_PLUS_OPTPATH,
    TaskPath,
    command,
    delete_and_rm_options,
    shlex_process_stdin,
    task_submission_options,
)
from globus_cli.safeio import (
    FORMAT_TEXT_RECORD,
    err_is_terminal,
    formatted_print,
    term_is_interactive,
)
from globus_cli.services.transfer import autoactivate, get_client


@command(
    "delete",
    short_help="Submit a delete task (asynchronous)",
    adoc_examples="""Delete a single file.

[source,bash]
----
$ ep_id=ddb59af0-6d04-11e5-ba46-22000b92c6ec
$ globus delete $ep_id:~/myfile.txt
----

Delete a directory recursively.

[source,bash]
----
$ ep_id=ddb59af0-6d04-11e5-ba46-22000b92c6ec
$ globus delete $ep_id:~/mydir --recursive
----

Use the batch input method to transfer multiple files and or dirs.

[source,bash]
----
$ ep_id=ddb59af0-6d04-11e5-ba46-22000b92c6ec
$ globus delete $ep_id --batch --recursive
~/myfile1.txt
~/myfile2.txt
~/myfile3.txt
~/mygodatadir
<EOF>
----

Submit a deletion task and get back the task ID for use in `globus task wait`:

[source,bash]
----
$ ep_id=ddb59af0-6d04-11e5-ba46-22000b92c6ec
$ task_id="$(globus delete $ep_id:~/mydir --recursive \
    --jmespath 'task_id' --format unix)"
$ echo "Waiting on $task_id"
$ globus task wait "$task_id"
----
""",
)
@task_submission_options
@delete_and_rm_options
@click.argument("endpoint_plus_path", type=ENDPOINT_PLUS_OPTPATH)
def delete_command(
    batch,
    ignore_missing,
    star_silent,
    recursive,
    enable_globs,
    endpoint_plus_path,
    label,
    submission_id,
    dry_run,
    deadline,
    skip_activation_check,
    notify,
):
    """
    Submits an asynchronous task that deletes files and/or directories on the target
    endpoint.

    *globus delete* has two modes. Single target, which deletes one
    file or one directory, and batch, which takes in several lines to delete
    multiple files or directories. See "Batch Input" below for more information.

    Symbolic links are never followed - only unlinked (deleted).

    === Batch Input

    If you give a SOURCE_PATH without the --batch flag, you will submit a
    single-file or single-directory delete task. This has
    behavior similar to `rm` and `rm -r`, across endpoints.

    Using `--batch`, *globus delete* can submit a task which deletes
    multiple files or directories. Lines are taken from stdin, respecting quotes,
    and every line is treated as a path to a file or directory to delete.

    \b
    Lines are of the form
      PATH

    Note that unlike 'globus transfer' --recursive is not an option at the per line
    level, instead, if given with the original command, all paths that point to
    directories will be recursively deleted.

    Empty lines and comments beginning with '#' are ignored.

    Batch only requires an ENDPOINT before passing lines, on stdin, but if you pass
    an ENPDOINT:PATH on the original command, this path will be used as a prefixes
    to all paths on stdin.

    {AUTOMATIC_ACTIVATION}
    """
    endpoint_id, path = endpoint_plus_path
    if path is None and (not batch):
        raise click.UsageError("delete requires either a PATH OR --batch")

    client = get_client()

    # attempt to activate unless --skip-activation-check is given
    if not skip_activation_check:
        autoactivate(client, endpoint_id, if_expires_in=60)

    delete_data = DeleteData(
        client,
        endpoint_id,
        label=label,
        recursive=recursive,
        ignore_missing=ignore_missing,
        submission_id=submission_id,
        deadline=deadline,
        skip_activation_check=skip_activation_check,
        interpret_globs=enable_globs,
        **notify
    )

    if batch:
        # although this sophisticated structure (like that in transfer)
        # isn't strictly necessary, it gives us the ability to add options in
        # the future to these lines with trivial modifications
        @click.command()
        @click.argument("path", type=TaskPath(base_dir=path))
        def process_batch_line(path):
            """
            Parse a line of batch input and add it to the delete submission
            item.
            """
            delete_data.add_item(str(path))

        shlex_process_stdin(process_batch_line, "Enter paths to delete, line by line.")
    else:
        if not star_silent and enable_globs and path.endswith("*"):
            # not intuitive, but `click.confirm(abort=True)` prints to stdout
            # unnecessarily, which we don't really want...
            # only do this check if stderr is a pty
            if (
                err_is_terminal()
                and term_is_interactive()
                and not click.confirm(
                    'Are you sure you want to delete all files matching "{}"?'.format(
                        path
                    ),
                    err=True,
                )
            ):
                click.echo("Aborted.", err=True)
                click.get_current_context().exit(1)
        delete_data.add_item(path)

    if dry_run:
        formatted_print(delete_data, response_key="DATA", fields=[("Path", "path")])
        # exit safely
        return

    res = client.submit_delete(delete_data)
    formatted_print(
        res,
        text_format=FORMAT_TEXT_RECORD,
        fields=(("Message", "message"), ("Task ID", "task_id")),
    )
