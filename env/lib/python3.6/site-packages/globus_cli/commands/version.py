from globus_cli.helpers import print_version
from globus_cli.parsing import command


@command(
    "version",
    disable_options=["format", "map_http_status"],
    short_help="Show the version and exit",
)
def version_command():
    """
    Displays the current and latest versions of the Globus CLI. Equivalent to
    'globus --version'

    If the current version is not the latest version, instructions will be given
    for how to update the CLI.
    """
    print_version()
