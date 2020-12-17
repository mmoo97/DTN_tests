import webbrowser

import click

from globus_cli.config import MYPROXY_USERNAME_OPTNAME, lookup_option
from globus_cli.helpers import (
    fill_delegate_proxy_activation_requirements,
    is_remote_session,
)
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.safeio import FORMAT_TEXT_RAW, formatted_print
from globus_cli.services.transfer import activation_requirements_help_text, get_client


@command(
    "activate",
    short_help="Activate an endpoint",
    adoc_examples="""Activate an endpoint using just Automatic activation:

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint activate $ep_id
----

Activate an endpoint using Web activation

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint activate $ep_id --web
----

Activate an endpoiont using Myproxy activation, skipping the username prompt.

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint activate $ep_id --myproxy -U username
----
""",
)
@endpoint_id_arg
@click.option(
    "--web",
    is_flag=True,
    default=False,
    help="Use web activation. Mutually exclusive with --myproxy  and --delegate-proxy.",
)
@click.option(
    "--no-browser",
    is_flag=True,
    default=False,
    help=(
        "If using --web, Give a url to manually follow instead of "
        "opening your default web browser. Implied if the CLI "
        "detects this is a remote session."
    ),
)
@click.option(
    "--myproxy",
    is_flag=True,
    default=False,
    help="Use myproxy activation. Mutually exclusive with --web and --delegate-proxy.",
)
@click.option(
    "--myproxy-username",
    "-U",
    help=(
        "Give a username to use with --myproxy. "
        "Overrides any default myproxy username set in config."
    ),
)
@click.option("--myproxy-password", "-P", hidden=True)
@click.option(
    "--myproxy-lifetime",
    type=int,
    help=(
        "The lifetime for the credential to request from the "
        "server under --myproxy activation, in hours. "
        "The myproxy server may be configured with a maximum "
        "lifetime which it will use if this value is too high"
    ),
)
@click.option(
    "--delegate-proxy",
    metavar="X.509_PEM_FILE",
    help=(
        "Use delegate proxy activation, takes an X.509 "
        "certificate in pem format as an argument. Mutually "
        "exclusive with --web and --myproxy."
    ),
)
@click.option(
    "--proxy-lifetime",
    type=int,
    default=None,
    help=(
        "Set a lifetime in hours for the proxy generated with "
        "--delegate-proxy. [default: 12]"
    ),
)
@click.option(
    "--no-autoactivate",
    is_flag=True,
    default=False,
    help=(
        "Don't attempt to autoactivate endpoint before using "
        "another activation method."
    ),
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force activation even if endpoint is already activated.",
)
def endpoint_activate(
    endpoint_id,
    myproxy,
    myproxy_username,
    myproxy_password,
    myproxy_lifetime,
    web,
    no_browser,
    delegate_proxy,
    proxy_lifetime,
    no_autoactivate,
    force,
):
    """
    Activate an endpoint using Autoactivation, Myproxy, Delegate Proxy,
    or Web activation.
    Note that --web, --delegate-proxy, and --myproxy activation are mutually
    exclusive options.

    \b
    Autoactivation will always be attempted unless the --no-autoactivate
    option is given. If autoactivation succeeds any other activation options
    will be ignored as the endpoint has already been successfully activated.

    \b
    To use Web activation use the --web option.
    The CLI will try to open your default browser to the endpoint's activation
    page, but if a remote CLI session is detected, or the --no-browser option
    is given, a url will be printed for you to manually follow and activate
    the endpoint.

    \b
    To use Myproxy activation give the --myproxy option.
    Myproxy activation requires your username and password for the myproxy
    server the endpoint is using for authentication. e.g. for default
    Globus Connect Server endpoints this will be your login credentials for the
    server the endpoint is hosted on.
    You can enter your username when prompted, give your username with the
    --myproxy-username option, or set a default myproxy username in config with
    "globus config init" or "globus config set cli.default_myproxy_username".
    For security it is recommended that you only enter your password when
    prompted to hide your inputs and keep your password out of your
    command history, but you may pass your password with the hidden
    --myproxy-password or -P options.

    \b
    To use Delegate Proxy activation use the --delegate-proxy option with a
    file containing an X.509 certificate as an argument (e.g. an X.509
    gotten from the myproxy-logon command). This certificate must
    be a valid credential or proxy credential for the user from an identity
    provider accepted by the endpoint being activated, and the endpoint must be
    configured with a gridmap that will match the globus user using this
    command with the local user the certificate was made to. Note if the X.509
    is valid, but the endpoint does not recognize the identity provider or the
    user the error will not be detected until the user attempts to perform an
    operation on the endpoint.
    """
    default_myproxy_username = lookup_option(MYPROXY_USERNAME_OPTNAME)
    client = get_client()

    # validate options
    if web + myproxy + bool(delegate_proxy) > 1:
        raise click.UsageError(
            "--web, --myproxy, and --delegate-proxy are mutually exclusive."
        )
    if no_autoactivate and not (myproxy or web or delegate_proxy):
        raise click.UsageError(
            "--no-autoactivate requires another activation method be given."
        )
    if myproxy_username and not myproxy:
        raise click.UsageError("--myproxy-username requires --myproxy.")
    if myproxy_password and not myproxy:
        raise click.UsageError("--myproxy-password requires --myproxy.")
    # NOTE: "0" is a legitimate, though weird, value
    # In the case where someone is setting this value programatically,
    # respecting it behaves more consistently/predictably
    if myproxy_lifetime is not None and not myproxy:
        raise click.UsageError("--myproxy-lifetime requires --myproxy.")
    if no_browser and not web:
        raise click.UsageError("--no-browser requires --web.")
    if proxy_lifetime and not delegate_proxy:
        raise click.UsageError("--proxy-lifetime requires --delegate-proxy.")

    # check if endpoint is already activated unless --force
    if not force:
        res = client.endpoint_autoactivate(endpoint_id, if_expires_in=60)

        if "AlreadyActivated" == res["code"]:
            formatted_print(
                res,
                simple_text=(
                    "Endpoint is already activated. Activation "
                    "expires at {}".format(res["expire_time"])
                ),
            )
            return

    # attempt autoactivation unless --no-autoactivate
    if not no_autoactivate:

        res = client.endpoint_autoactivate(endpoint_id)

        if "AutoActivated" in res["code"]:
            formatted_print(
                res,
                simple_text=(
                    "Autoactivation succeeded with message: {}".format(res["message"])
                ),
            )
            return

        # override potentially confusing autoactivation failure response
        else:
            message = (
                "The endpoint could not be auto-activated.\n\n"
                + activation_requirements_help_text(res, endpoint_id)
            )
            res = {"message": message}

    # myproxy activation
    if myproxy:
        # fetch activation requirements
        requirements_data = client.endpoint_get_activation_requirements(
            endpoint_id
        ).data
        # filter to the myproxy requirements; ensure that there are values
        myproxy_requirements_data = [
            x for x in requirements_data["DATA"] if x["type"] == "myproxy"
        ]
        if not len(myproxy_requirements_data):
            raise click.ClickException(
                "This endpoint does not support myproxy activation"
            )

        # get username and password
        if not (myproxy_username or default_myproxy_username):
            myproxy_username = click.prompt("Myproxy username")
        if not myproxy_password:
            myproxy_password = click.prompt("Myproxy password", hide_input=True)

        # fill out the requirements data -- note that because everything has been done
        # by reference, `requirements_data` still refers to the document containing
        # these values
        for data in myproxy_requirements_data:
            if data["name"] == "passphrase":
                data["value"] = myproxy_password
            if data["name"] == "username":
                data["value"] = myproxy_username or default_myproxy_username
            if data["name"] == "hostname" and data["value"] is None:
                raise click.ClickException(
                    "This endpoint has no myproxy server "
                    "and so cannot be activated through myproxy"
                )
            # NOTE: remember that "0" is a possible value
            if data["name"] == "lifetime_in_hours" and myproxy_lifetime is not None:
                data["value"] = str(myproxy_lifetime)

        res = client.endpoint_activate(endpoint_id, requirements_data)

    # web activation
    elif web:
        url = "https://app.globus.org/file-manager?origin_id={}".format(endpoint_id)
        if no_browser or is_remote_session():
            res = {"message": "Web activation url: {}".format(url), "url": url}
        else:
            webbrowser.open(url, new=1)
            res = {"message": "Browser opened to web activation page", "url": url}

    # delegate proxy activation
    elif delegate_proxy:
        requirements_data = client.endpoint_get_activation_requirements(
            endpoint_id
        ).data
        filled_requirements_data = fill_delegate_proxy_activation_requirements(
            requirements_data, delegate_proxy, lifetime_hours=proxy_lifetime or 12
        )
        res = client.endpoint_activate(endpoint_id, filled_requirements_data)

    # output
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
