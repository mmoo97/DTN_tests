import json

import click

from globus_cli.parsing import command, task_id_arg
from globus_cli.safeio import formatted_print
from globus_cli.services.transfer import get_client, iterable_response_to_dict


@command(
    "event-list",
    short_help="List events for a given task",
    adoc_synopsis="""
`globus task event-list [OPTIONS] TASK_ID`

`globus task event-list --filter-errors [OPTIONS] TASK_ID`

`globus task event-list --filter-non-errors [OPTIONS] TASK_ID`
""",
    adoc_output="""When output is in text mode, the following fields are used:

- 'Time'
- 'Code'
- 'Is Error'
- 'Details'
""",
    adoc_examples="""Show why a task is paused, producing JSON output:

[source,bash]
----
$ globus task pause-info TASK_ID --format JSON
----
""",
)
@task_id_arg
@click.option("--limit", default=10, show_default=True, help="Limit number of results.")
@click.option("--filter-errors", is_flag=True, help="Filter results to errors")
@click.option("--filter-non-errors", is_flag=True, help="Filter results to non errors")
def task_event_list(task_id, limit, filter_errors, filter_non_errors):
    """
    This command shows the recent events for a running task.
    Most events of interest are fault events, which are errors which occurred on an
    endpoint but which are non-fatal to a task. For example, Permission Denied errors
    on an endpoint don't cancel the task because they are often resolvable -- at which
    point the task would retry succeed.

    Events may be filtered using '--filter-errors' or '--filter-non-errors', but
    these two options may not be used in tandem.

    NOTE: Tasks older than one month may no longer have event log history. In this
    case, no events will be shown.
    """
    client = get_client()

    # cannot filter by both errors and non errors
    if filter_errors and filter_non_errors:
        raise click.UsageError("Cannot filter by both errors and non errors")

    elif filter_errors:
        filter_string = "is_error:1"

    elif filter_non_errors:
        filter_string = "is_error:0"

    else:
        filter_string = ""

    event_iterator = client.task_event_list(
        task_id, num_results=limit, filter=filter_string
    )

    def squashed_json_details(x):
        is_json = False
        try:
            loaded = json.loads(x["details"])
            is_json = True
        except ValueError:
            loaded = x["details"]

        if is_json:
            return json.dumps(loaded, separators=(",", ":"), sort_keys=True)
        else:
            return loaded.replace("\n", "\\n")

    formatted_print(
        event_iterator,
        fields=(
            ("Time", "time"),
            ("Code", "code"),
            ("Is Error", "is_error"),
            ("Details", squashed_json_details),
        ),
        json_converter=iterable_response_to_dict,
    )
