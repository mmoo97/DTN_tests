import click

from globus_cli.parsing import command, task_id_arg
from globus_cli.safeio import FORMAT_TEXT_RAW, formatted_print
from globus_cli.services.transfer import get_client


@command(
    "cancel",
    short_help="Cancel a task",
    adoc_synopsis="""
`globus task cancel [OPTIONS] TASK_ID`

`globus task cancel --all [OPTIONS]`
""",
    adoc_output="""
Output depends on whether or not '--all' was provided, and of course on the
requested output format.

If '--all' is requested, output will contain all task IDs which were
cancelled. If, in addition to this, the output format is text, the results will
be streamed as tasks are cancelled. JSON output is buffered and printed all at
once, after all of the cancellations.

When '--all' is not passed, output is a simple success message indicating that
the task was cancelled, or an error.
""",
    adoc_examples="""Cancel a specific task

[source,bash]
----
$ globus task cancel TASK_ID
----

Cancel all tasks

[source,bash]
----
$ globus task cancel --all
----
""",
)
@task_id_arg(required=False)
@click.option(
    "--all", "-a", is_flag=True, help="Cancel all in-progress tasks that you own"
)
def cancel_task(all, task_id):
    """
    Cancel a task you own or all tasks which you own.

    This includes not only currently executing tasks, but also any queued tasks which
    you may have which have not started execution.

    You must either provide the '--all' option or a 'TASK_ID'.
    """

    if bool(all) + bool(task_id) != 1:
        raise click.UsageError(
            "You must pass EITHER the special --all flag "
            "to cancel all in-progress tasks OR a single "
            "task ID to cancel."
        )

    client = get_client()

    if all:
        from sys import maxsize

        task_ids = [
            task_row["task_id"]
            for task_row in client.task_list(
                filter="type:TRANSFER,DELETE/status:ACTIVE,INACTIVE",
                fields="task_id",
                num_results=maxsize,  # FIXME want to ask for "unlimited" set
            )
        ]

        task_count = len(task_ids)

        if not task_ids:
            raise click.ClickException("You have no in-progress tasks.")

        def cancellation_iterator():
            for i in task_ids:
                yield (i, client.cancel_task(i).data)

        def json_converter(res):
            return {
                "results": [x for i, x in cancellation_iterator()],
                "task_ids": task_ids,
            }

        def _custom_text(res):
            for (i, (task_id, data)) in enumerate(cancellation_iterator(), start=1):
                click.echo(
                    u"{} ({} of {}): {}".format(task_id, i, task_count, data["message"])
                )

        # FIXME: this is kind of an abuse of formatted_print because the
        # text format and json converter are doing their own thing, not really
        # interacting with the "response data" (None). Is there a better way of
        # handling this?
        formatted_print(None, text_format=_custom_text, json_converter=json_converter)

    else:
        res = client.cancel_task(task_id)
        formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
