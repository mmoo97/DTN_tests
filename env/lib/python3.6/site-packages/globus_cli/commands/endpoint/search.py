import click

from globus_cli.parsing import command
from globus_cli.safeio import formatted_print
from globus_cli.services.auth import maybe_lookup_identity_id
from globus_cli.services.transfer import (
    ENDPOINT_LIST_FIELDS,
    get_client,
    iterable_response_to_dict,
)


@command(
    "search",
    short_help="Find and discover endpoints",
    adoc_synopsis="""
`globus endpoint search [OPTIONS] FILTER_FULLTEXT`

`globus endpoint search --filter-scope SCOPE [OPTIONS] [FILTER_FULLTEXT]`
""",
    adoc_examples="""Search for the Globus tutorial endpoints

[source,bash]
----
$ globus endpoint search Tutorial --filter-owner-id go@globusid.org
----

Search for endpoints owned by the current user

[source,bash]
----
$ globus endpoint search --filter-scope my-endpoints
----
""",
)
@click.option(
    "--filter-scope",
    default="all",
    show_default=True,
    type=click.Choice(
        (
            "all",
            "administered-by-me",
            "my-endpoints",
            "my-gcp-endpoints",
            "recently-used",
            "in-use",
            "shared-by-me",
            "shared-with-me",
        ),
        case_sensitive=False,
    ),
    help="The set of endpoints to search over.",
)
@click.option(
    "--filter-owner-id",
    help=(
        "Filter search results to endpoints owned by a specific "
        "identity. Can be the Identity ID, or the Identity "
        'Username, as in "go@globusid.org"'
    ),
)
@click.option(
    "--limit",
    default=25,
    show_default=True,
    type=click.IntRange(1, 1000),
    help="The maximum number of results to return.",
)
@click.argument("filter_fulltext", required=False)
def endpoint_search(filter_fulltext, limit, filter_owner_id, filter_scope):
    """
    Search for Globus endpoints with search filters. If --filter-scope is set to the
    default of 'all', then FILTER_FULLTEXT is required.

    If FILTER_FULLTEXT is given, endpoints which have attributes (display name,
    legacy name, description, organization, department, keywords) that match the
    search text will be returned. The result size limit is 100 endpoints.
    """
    if filter_scope == "all" and not filter_fulltext:
        raise click.UsageError(
            "When searching all endpoints (--filter-scope=all, the default), "
            "a full-text search filter is required. Other scopes (e.g. "
            "--filter-scope=recently-used) may be used without specifying "
            "an additional filter."
        )

    client = get_client()

    owner_id = filter_owner_id
    if owner_id:
        owner_id = maybe_lookup_identity_id(owner_id)

    search_iterator = client.endpoint_search(
        filter_fulltext=filter_fulltext,
        filter_scope=filter_scope,
        filter_owner_id=owner_id,
        num_results=limit,
    )

    formatted_print(
        search_iterator,
        fields=ENDPOINT_LIST_FIELDS,
        json_converter=iterable_response_to_dict,
    )

    if search_iterator.limit_less_than_available_results:
        click.echo(
            click.style(
                """
WARNING: More results were available from the Endpoint Search API, but you
         specified a limit lower than the number of available results
""",
                fg="yellow",
            ),
            err=True,
        )
