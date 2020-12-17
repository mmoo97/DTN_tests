import sys

import click

from globus_cli.parsing.excepthook import custom_except_hook


class GlobusCommand(click.Command):
    """
    A custom command class which stores the special attributes
    of the form "adoc_*" with defaults of None. This lets us pass additional info to the
    adoc generator.

    It also automatically runs string formatting on command helptext to allow the
    inclusion of common strings (e.g. autoactivation help).
    """

    AUTOMATIC_ACTIVATION_HELPTEXT = """=== Automatic Endpoint Activation

This command requires all endpoints it uses to be activated. It will attempt to
auto-activate any endpoints that are not active, but if auto-activation fails,
you will need to manually activate the endpoint. See 'globus endpoint activate'
for more details."""

    def __init__(self, *args, **kwargs):
        self.adoc_skip = kwargs.pop("adoc_skip", False)
        self.adoc_output = kwargs.pop("adoc_output", None)
        self.adoc_examples = kwargs.pop("adoc_examples", None)
        self.globus_disable_opts = kwargs.pop("globus_disable_opts", [])
        self.adoc_exit_status = kwargs.pop("adoc_exit_status", None)
        self.adoc_synopsis = kwargs.pop("adoc_synopsis", None)

        helptext = kwargs.pop("help", None)
        if helptext:
            kwargs["help"] = helptext.format(
                AUTOMATIC_ACTIVATION=self.AUTOMATIC_ACTIVATION_HELPTEXT
            )
        super(GlobusCommand, self).__init__(*args, **kwargs)


class GlobusCommandGroup(click.Group):
    """
    This is a click.Group with any customizations which we deem necessary
    *everywhere*.

    In particular, at present it provides a better form of handling for
    no_args_is_help. If that flag is set, helptext will be triggered not only
    off of cases where there are no arguments at all, but also cases where
    there are options, but no subcommand (positional arg) is given.
    """

    def invoke(self, ctx):
        # if no subcommand was given (but, potentially, flags were passed),
        # ctx.protected_args will be empty
        # improves upon the built-in detection given on click.Group by
        # no_args_is_help , since that treats options (without a subcommand) as
        # being arguments and blows up with a "Missing command" failure
        # for reference to the original version (as of 2017-02-26):
        # https://github.com/pallets/click/blob/02ea9ee7e864581258b4902d6e6c1264b0226b9f/click/core.py#L1039-L1052
        if self.no_args_is_help and not ctx.protected_args:
            click.echo(ctx.get_help())
            ctx.exit()
        return super(GlobusCommandGroup, self).invoke(ctx)


class TopLevelGroup(GlobusCommandGroup):
    """
    This is a custom command type which is basically a click.Group, but is
    designed specifically for the top level command.
    It's specialization is that it catches all exceptions from subcommands and
    passes them to a custom error handler.
    """

    def invoke(self, ctx):
        try:
            return super(TopLevelGroup, self).invoke(ctx)
        except Exception:
            custom_except_hook(sys.exc_info())
