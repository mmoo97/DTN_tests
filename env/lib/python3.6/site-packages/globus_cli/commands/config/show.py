import click

from globus_cli.config import lookup_option
from globus_cli.parsing import command


@command("show", disable_options=["format"], adoc_skip=True)
@click.argument("parameter", required=True)
def show_command(parameter):
    """Show a value from the Globus config file"""
    section = "cli"
    if "." in parameter:
        section, parameter = parameter.split(".", 1)

    value = lookup_option(parameter, section=section)

    if value is None:
        click.echo("{} not set".format(parameter))
    else:
        click.echo("{} = {}".format(parameter, value))
