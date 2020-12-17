from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.safeio import FORMAT_TEXT_RECORD, FORMAT_TEXT_TABLE, formatted_print
from globus_cli.services.transfer import get_endpoint_w_server_list


@command(
    "list",
    short_help="List all servers for an endpoint",
    adoc_examples="""[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint server list $ep_id
----
""",
)
@endpoint_id_arg
def server_list(endpoint_id):
    """List all servers belonging to an endpoint."""
    # raises usage error on shares for us
    endpoint, server_list = get_endpoint_w_server_list(endpoint_id)

    if server_list == "S3":  # not GCS -- this is an S3 endpoint
        server_list = {"s3_url": endpoint["s3_url"]}
        fields = [("S3 URL", "s3_url")]
        text_format = FORMAT_TEXT_RECORD
    else:  # regular GCS host endpoint
        fields = (
            ("ID", "id"),
            ("URI", lambda s: (s["uri"] or "none (Globus Connect Personal)")),
        )
        text_format = FORMAT_TEXT_TABLE
    formatted_print(server_list, text_format=text_format, fields=fields)
