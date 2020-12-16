"""
This module defines all of the tools needed to decorate the top-level `globus`
command. All customizations that apply specifically to this main command go
here.
Ultimately, `globus_cli.parsing` will export only the decorator defined here,
and all other components will be hidden internals.
"""

import click

from globus_cli.parsing.custom_classes import (
    GlobusCommand,
    GlobusCommandGroup,
    TopLevelGroup,
)
from globus_cli.parsing.shared_options import common_options
from globus_cli.parsing.shell_completion import print_completer_option


def main_group(f):
    f = click.group("globus", cls=TopLevelGroup, help=f.__doc__)(f)
    f = common_options(f)
    f = print_completer_option(f)
    return f


def command(*args, **kwargs):
    """
    A helper for decorating commands a-la `click.command`, but pulling the help string
    from `<function>.__doc__` by default.

    Also allows the use of custom arguments, which are stored on the command, as in
    "adoc_examples".
    """
    disable_opts = kwargs.pop("disable_options", [])

    def _inner_decorator(func):
        if "help" not in kwargs:
            kwargs["help"] = func.__doc__

        if "cls" not in kwargs:
            kwargs["cls"] = GlobusCommand

        kwargs["globus_disable_opts"] = disable_opts

        return common_options(disable_options=disable_opts)(
            click.command(*args, **kwargs)(func)
        )

    return _inner_decorator


def group(*args, **kwargs):
    """
    Wrapper over click.group which sets GlobusCommandGroup as the Class

    Caution!
    Don't get snake-bitten by this. `group` is a decorator which MUST
    take arguments. It is not wrapped in our common detect-and-decorate pattern
    to allow it to be used bare -- that wouldn't work (unnamed groups? weird
    stuff)
    """
    disable_opts = kwargs.pop("disable_options", [])

    def inner_decorator(f):
        f = click.group(*args, cls=GlobusCommandGroup, **kwargs)(f)
        if "help" not in kwargs:
            kwargs["help"] = f.__doc__
        f = common_options(disable_options=disable_opts)(f)
        return f

    return inner_decorator
