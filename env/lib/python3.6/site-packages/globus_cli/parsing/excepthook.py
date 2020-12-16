"""
Setup a custom except hook which formats exceptions that are uncaught.
In "DEBUGMODE", we'll just use the typical sys.excepthook behavior and print a
stacktrace. It's really for debugging problems with the CLI itself, but it
might also come in handy if we have issues with the way that we're trying to
format an exception.
Define an except hook per exception type that we want to treat specially,
generally types of SDK errors, and dispatch onto tht set of hooks.
"""
import sys

import click
import click.exceptions
from globus_sdk import exc
from six import reraise

from globus_cli.parsing.command_state import CommandState
from globus_cli.safeio import PrintableErrorField, write_error_info


def exit_with_mapped_status(http_status):
    """
    Given an HTTP Status, exit with either an error status of 1 or the
    status mapped by what we were given.
    """
    # get the mapping by looking up the state and getting the mapping attr
    mapping = click.get_current_context().ensure_object(CommandState).http_status_map

    # if there is a mapped exit code, exit with that. Otherwise, exit 1
    if http_status in mapping:
        sys.exit(mapping[http_status])
    else:
        sys.exit(1)


def session_hook(exception):
    """
    Expects an exception with an authorization_paramaters field in its raw_json
    """
    click.echo(
        "The resource you are trying to access requires you to "
        "re-authenticate with specific identities."
    )

    params = exception.raw_json["authorization_parameters"]
    message = params.get("session_message")
    if message:
        click.echo("message: {}".format(message))

    identities = params.get("session_required_identities")
    if identities:
        id_str = " ".join(identities)
        click.echo(
            "Please run\n\n"
            "    globus session update {}\n\n"
            "to re-authenticate with the required identities".format(id_str)
        )
    else:
        click.echo(
            'Please use "globus session update" to re-authenticate '
            "with specific identities"
        )

    exit_with_mapped_status(exception.http_status)


def consent_required_hook(exception):
    """
    Expects an exception with a required_scopes field in its raw_json
    """
    message = exception.raw_json.get("message")

    # specialized message for data_access errors
    # otherwise, use more generic phrasing
    if message == "Missing required data_access consent":
        click.echo(
            "The collection you are trying to access data on requires you to "
            "grant consent for the Globus CLI to access it."
        )
    else:
        click.echo(
            "The resource you are trying to access requires you to "
            "consent to additional access for the Globus CLI."
        )

    required_scopes = exception.raw_json.get("required_scopes")
    if not required_scopes:
        click.secho(
            "Fatal Error: ConsentRequired but no required_scopes!", bold=True, fg="red"
        )
        sys.exit(255)
    if message:
        click.echo("message: {}".format(message))

    click.echo(
        "\nPlease run\n\n"
        "  globus session consent {}\n\n".format(
            " ".join("'{}'".format(x) for x in required_scopes)
        )
        + "to login with the required scopes"
    )
    exit_with_mapped_status(exception.http_status)


def transferapi_hook(exception):
    write_error_info(
        "Transfer API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("request_id", exception.request_id),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )
    exit_with_mapped_status(exception.http_status)


def authapi_hook(exception):
    write_error_info(
        "Auth API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )
    exit_with_mapped_status(exception.http_status)


def globusapi_hook(exception):
    write_error_info(
        "Globus API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )
    exit_with_mapped_status(exception.http_status)


def authentication_hook(exception):
    write_error_info(
        "No Authentication Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
        message=(
            "Globus CLI Error: No Authentication provided. Make sure "
            "you have logged in with 'globus login'."
        ),
    )
    exit_with_mapped_status(exception.http_status)


def invalidrefresh_hook(exception):
    write_error_info(
        "Invalid Refresh Token",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
        message=(
            "Globus CLI Error: Your credentials are no longer "
            "valid. Please log in again with 'globus login'."
        ),
    )
    exit_with_mapped_status(exception.http_status)


def globus_generic_hook(exception):
    write_error_info(
        "Globus Error",
        [
            PrintableErrorField("error_type", exception.__class__.__name__),
            PrintableErrorField("message", str(exception), multiline=True),
        ],
    )
    sys.exit(1)


def custom_except_hook(exc_info):
    """
    A custom excepthook to present python errors produced by the CLI.
    We don't want to show end users big scary stacktraces if they aren't python
    programmers, so slim it down to some basic info. We keep a "DEBUGMODE" env
    variable kicking around to let us turn on stacktraces if we ever need them.
    """
    exception_type, exception, traceback = exc_info

    # check if we're in debug mode, and run the real excepthook if we are
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    if state.debug:
        sys.excepthook(exception_type, exception, traceback)

    # we're not in debug mode, do custom handling

    # catch any session errors to give helpful instructions
    # on how to use globus session update
    if (
        isinstance(exception, exc.GlobusAPIError)
        and exception.raw_json
        and "authorization_parameters" in exception.raw_json
    ):
        session_hook(exception)

    # catch any consent required errors to give helpful instructions
    # on how to use `globus session update --consents`
    if (
        isinstance(exception, exc.GlobusAPIError)
        and exception.raw_json
        and exception.raw_json.get("code") == "ConsentRequired"
    ):
        consent_required_hook(exception)

    # handle the Globus-raised errors with our special hooks
    # these will present the output (on stderr) as JSON
    elif isinstance(exception, exc.TransferAPIError):
        if exception.code == "ClientError.AuthenticationFailed":
            authentication_hook(exception)
        else:
            transferapi_hook(exception)

    elif isinstance(exception, exc.AuthAPIError):
        if exception.code == "UNAUTHORIZED":
            authentication_hook(exception)
        # invalid_grant occurs when the users refresh tokens are not valid
        elif exception.message == "invalid_grant":
            invalidrefresh_hook(exception)
        else:
            authapi_hook(exception)

    elif isinstance(exception, exc.GlobusAPIError):
        globusapi_hook(exception)

    # specific checks fell through -- now check if it's any kind of
    # GlobusError
    elif isinstance(exception, exc.GlobusError):
        globus_generic_hook(exception)

    # if it's a click exception, re-raise as original -- Click's main
    # execution context will handle pretty-printing
    elif isinstance(
        exception, (click.ClickException, click.exceptions.Abort, click.exceptions.Exit)
    ):
        reraise(exception_type, exception, traceback)

    # not a GlobusError, not a ClickException -- something like ValueError
    # or NotImplementedError bubbled all the way up here: just print it
    # out, basically
    else:
        click.echo(
            u"{}: {}".format(
                click.style(exception_type.__name__, bold=True, fg="red"), exception
            )
        )
        sys.exit(1)
