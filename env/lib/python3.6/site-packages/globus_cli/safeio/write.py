import click

from globus_cli.safeio.check_pty import (
    err_is_terminal,
    out_is_terminal,
    term_is_interactive,
)


def print_command_hint(message):
    """
    Wrapper around echo that checks terminal state
    before printing a given command hint message
    """
    if term_is_interactive() and err_is_terminal() and out_is_terminal():
        click.echo(click.style(message, fg="yellow"), err=True)
