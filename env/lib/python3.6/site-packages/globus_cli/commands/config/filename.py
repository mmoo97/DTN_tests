import click

from globus_cli.config import get_config_obj
from globus_cli.parsing import command


@command("filename", disable_options=["format", "map_http_status"], adoc_skip=True)
def filename_command():
    """Output the path of the config file"""
    try:
        config = get_config_obj(file_error=True)
    except IOError as e:
        click.echo(e, err=True)
        click.get_current_context().exit(1)
    else:
        click.echo(config.filename)
