import os
import sys


def out_is_terminal():
    return sys.stdout.isatty()


def err_is_terminal():
    return sys.stderr.isatty()


def term_is_interactive():
    return os.getenv("PS1") is not None
