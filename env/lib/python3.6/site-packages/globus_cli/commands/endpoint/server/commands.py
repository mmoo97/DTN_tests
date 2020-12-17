from globus_cli.commands.endpoint.server.add import server_add
from globus_cli.commands.endpoint.server.delete import server_delete
from globus_cli.commands.endpoint.server.list import server_list
from globus_cli.commands.endpoint.server.show import server_show
from globus_cli.commands.endpoint.server.update import server_update
from globus_cli.parsing import group


@group("server", short_help="Manage servers for a Globus endpoint")
def server_command():
    """
    Manage the servers which back a Globus endpoint

    This typically refers to a Globus Connect Server endpoint running on multiple
    servers. Each GridFTP server is registered as a server backing the endpoint.
    """


server_command.add_command(server_list)
server_command.add_command(server_show)
server_command.add_command(server_add)
server_command.add_command(server_update)
server_command.add_command(server_delete)
