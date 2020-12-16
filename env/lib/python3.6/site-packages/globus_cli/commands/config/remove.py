import click

from globus_cli.config import get_config_obj
from globus_cli.parsing import command


@command("remove", disable_options=["format"], adoc_skip=True)
@click.argument("parameter", required=True)
def remove_command(parameter):
    """Remove a value from the Globus config file"""
    conf = get_config_obj()

    section = "cli"
    if "." in parameter:
        section, parameter = parameter.split(".", 1)

    # ensure that the section exists
    if section not in conf:
        conf[section] = {}
    # remove the value for the given parameter
    del conf[section][parameter]

    # write to disk
    click.echo("Writing updated config to {}".format(conf.filename))
    conf.write()
