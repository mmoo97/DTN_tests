from globus_cli.parsing import command, endpoint_id_arg, server_add_and_update_opts
from globus_cli.safeio import FORMAT_TEXT_RAW, formatted_print
from globus_cli.services.transfer import assemble_generic_doc, get_client


@command(
    "add",
    short_help="Add a server to an endpoint",
    adoc_examples="""Add a server with a url of gridftp.example.org to an endpoint

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint server add $ep_id --hostname gridftp.example.org
----
""",
)
@server_add_and_update_opts(add=True)
@endpoint_id_arg
def server_add(
    endpoint_id,
    subject,
    port,
    scheme,
    hostname,
    incoming_data_ports,
    outgoing_data_ports,
):
    """
    Add a server to an endpoint.

    An endpoint must be a Globus Connect Server endpoint to have servers.
    """
    client = get_client()

    server_doc = assemble_generic_doc(
        "server", subject=subject, port=port, scheme=scheme, hostname=hostname
    )

    # n.b. must be done after assemble_generic_doc(), as that function filters
    # out `None`s, which we need to be able to set for `'unspecified'`
    if incoming_data_ports:
        server_doc.update(
            incoming_data_port_start=incoming_data_ports[0],
            incoming_data_port_end=incoming_data_ports[1],
        )
    if outgoing_data_ports:
        server_doc.update(
            outgoing_data_port_start=outgoing_data_ports[0],
            outgoing_data_port_end=outgoing_data_ports[1],
        )

    res = client.add_endpoint_server(endpoint_id, server_doc)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
