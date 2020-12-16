from globus_cli.commands.bookmark.create import bookmark_create
from globus_cli.commands.bookmark.delete import bookmark_delete
from globus_cli.commands.bookmark.list import bookmark_list
from globus_cli.commands.bookmark.rename import bookmark_rename
from globus_cli.commands.bookmark.show import bookmark_show
from globus_cli.parsing import group


@group("bookmark")
def bookmark_command():
    """Manage endpoint bookmarks"""


bookmark_command.add_command(bookmark_list)
bookmark_command.add_command(bookmark_create)
bookmark_command.add_command(bookmark_delete)
bookmark_command.add_command(bookmark_rename)
bookmark_command.add_command(bookmark_show)
