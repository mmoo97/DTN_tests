import os.path
import textwrap

import click

from globus_cli.config import (
    MYPROXY_USERNAME_OPTNAME,
    OUTPUT_FORMAT_OPTNAME,
    write_option,
)
from globus_cli.parsing import command


@command(
    "init",
    short_help="Initialize all settings in the Globus Config file",
    disable_options=["format"],
    adoc_skip=True,
)
@click.option(
    "--default-output-format",
    help="The default format for the CLI to use when printing.",
    type=click.Choice(["json", "text"], case_sensitive=False),
)
@click.option(
    "--default-myproxy-username",
    help="The default username to use when activating via myproxy.",
)
def init_command(default_output_format, default_myproxy_username):
    """
    Initialize your Clobus Config file with a series of prompts or passed
    options to set values used by the Globus CLI.

    Current settings that can be configured are:

    output_format: either 'text' for normal output or 'json' to display
    the machine parsable json used in the underlying Globus API.

    default_myproxy_username: a default username to use with 'globus endpoint
    activate --myproxy' If this value is set, the username prompt will be skipped
    when using myproxy authorization. This value can be overridden with an
    explicit use of --myproxy-username.
    """
    # now handle the output format, requires a little bit more care
    # first, prompt if it isn't given, but be clear that we have a sensible
    # default if they don't set it
    # then, make sure that if it is given, it's a valid format (discard
    # otherwise)
    # finally, set it only if given and valid
    if not default_output_format:
        click.echo(
            textwrap.fill(
                'This must be one of "json" or "text". Other values will be '
                "ignored. ENTER to skip."
            )
        )
        default_output_format = (
            click.prompt(
                "Default CLI output format (cli.output_format)", default="text"
            )
            .strip()
            .lower()
        )
        if default_output_format not in ("json", "text"):
            default_output_format = None

    if not default_myproxy_username:
        click.echo(textwrap.fill("ENTER to skip."))
        default_myproxy_username = click.prompt(
            "Default myproxy username (cli.default_myproxy_username)",
            default="",
            show_default=False,
        ).strip()

    # write to disk
    click.echo(
        "\n\nWriting updated config to {0}".format(os.path.expanduser("~/.globus.cfg"))
    )
    write_option(OUTPUT_FORMAT_OPTNAME, default_output_format)
    write_option(MYPROXY_USERNAME_OPTNAME, default_myproxy_username)
