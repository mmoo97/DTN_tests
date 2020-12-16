import click

from globus_cli.helpers import print_version


def version_option(f):
    """
    Largely a custom clone of click.version_option -- almost identical, but
    prints our special output.
    """

    def callback(ctx, param, value):
        # copied from click.decorators.version_option
        # no idea what resilient_parsing means, but...
        if not value or ctx.resilient_parsing:
            return

        print_version()
        ctx.exit(0)

    return click.option(
        "--version",
        is_flag=True,
        expose_value=False,
        is_eager=True,
        callback=callback,
        hidden=True,
    )(f)
