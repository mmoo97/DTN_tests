from globus_cli.commands.session.consent import session_consent
from globus_cli.commands.session.show import session_show
from globus_cli.commands.session.update import session_update
from globus_cli.parsing import group


@group("session")
def session_command():
    """Manage your CLI auth session"""


# commands
session_command.add_command(session_update)
session_command.add_command(session_show)
session_command.add_command(session_consent)
