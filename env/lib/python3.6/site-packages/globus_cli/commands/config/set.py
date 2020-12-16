import click

from globus_cli.config import get_config_obj
from globus_cli.parsing import command


@command("set", disable_options=["format"], adoc_skip=True)
@click.argument("parameter", required=True)
@click.argument("value", required=True)
def set_command(value, parameter):
    """Set a value in the Globus config file"""
    conf = get_config_obj()

    section = "cli"
    if "." in parameter:
        section, parameter = parameter.split(".", 1)

    # ensure that the section exists
    if section not in conf:
        conf[section] = {}
    # set the value for the given parameter
    conf[section][parameter] = value

    # write to disk
    click.echo("Writing updated config to {}".format(conf.filename))
    conf.write()
