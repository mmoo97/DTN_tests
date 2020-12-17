from globus_cli.commands.config.filename import filename_command
from globus_cli.commands.config.init import init_command
from globus_cli.commands.config.remove import remove_command
from globus_cli.commands.config.set import set_command
from globus_cli.commands.config.show import show_command
from globus_cli.parsing import group


@group("config", short_help="Manage your Globus config file. (Advanced Users)")
def config_command():
    """Manage your Globus config file.

    Be aware that these commands are for advanced users with a strong
    understanding of the underlying Globus API.

    Many commands accept PARAMETER names which identify settings in the
    config file. If a PARAMETER includes any dots '.', the part prior to its
    first dot is used as the config section name, and the remainder is the
    name of an option in that section.

    The default section name is 'cli', which is where most config values
    used by the Globus CLI are kept.

    \b
    For example, you might use
        $ globus config show output_format
    to display your current 'output_format' from the 'cli' section.
    You can equally well use
        $ globus config show cli.output_format
    to show the same value more explicitly.
    """


config_command.add_command(filename_command)
config_command.add_command(init_command)
config_command.add_command(remove_command)
config_command.add_command(set_command)
config_command.add_command(show_command)
