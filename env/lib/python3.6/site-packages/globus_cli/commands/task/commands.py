from globus_cli.commands.task.cancel import cancel_task
from globus_cli.commands.task.event_list import task_event_list
from globus_cli.commands.task.generate_submission_id import generate_submission_id
from globus_cli.commands.task.list import task_list
from globus_cli.commands.task.pause_info import task_pause_info
from globus_cli.commands.task.show import show_task
from globus_cli.commands.task.update import update_task
from globus_cli.commands.task.wait import task_wait
from globus_cli.parsing import group


@group("task")
def task_command():
    """Manage asynchronous tasks"""


task_command.add_command(task_list)
task_command.add_command(show_task)
task_command.add_command(update_task)
task_command.add_command(cancel_task)
task_command.add_command(task_event_list)
task_command.add_command(task_pause_info)
task_command.add_command(task_wait)
task_command.add_command(generate_submission_id)
