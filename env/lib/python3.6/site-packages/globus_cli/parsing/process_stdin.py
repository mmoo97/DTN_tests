import shlex
import sys

import click


def shlex_process_stdin(process_command, helptext):
    """
    Use shlex to process stdin line-by-line.
    Also prints help text.

    Requires that @process_command be a Click command object, used for
    processing single lines of input. helptext is prepended to the standard
    message printed to interactive sessions.
    """
    # if input is interactive, print help to stderr
    if sys.stdin.isatty():
        click.echo(
            (
                "{}\n".format(helptext) + "Lines are split with shlex in POSIX mode: "
                "https://docs.python.org/library/shlex.html#parsing-rules\n"
                "Terminate input with Ctrl+D or <EOF>\n"
            ),
            err=True,
        )

    # use readlines() rather than implicit file read line looping to force
    # python to properly capture EOF (otherwise, EOF acts as a flush and
    # things get weird)
    for line in sys.stdin.readlines():
        # get the argument vector:
        # do a shlex split to handle quoted paths with spaces in them
        # also lets us have comments with #
        argv = shlex.split(line, comments=True)
        if argv:
            try:
                process_command.main(args=argv)
            except SystemExit as e:
                if e.code != 0:
                    raise
