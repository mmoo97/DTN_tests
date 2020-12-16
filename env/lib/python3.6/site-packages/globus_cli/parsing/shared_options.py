import functools

import click

from globus_cli.parsing.command_state import (
    debug_option,
    format_option,
    map_http_status_option,
    verbose_option,
)
from globus_cli.parsing.detect_and_decorate import detect_and_decorate
from globus_cli.parsing.explicit_null import EXPLICIT_NULL
from globus_cli.parsing.location import LocationType
from globus_cli.parsing.version_option import version_option


def common_options(*args, **kwargs):
    """
    This is a multi-purpose decorator for applying a "base" set of options
    shared by all commands.
    It can be applied either directly, or given keyword arguments.

    Usage:

    >>> @common_options
    >>> def mycommand(abc, xyz):
    >>>     ...

    or

    >>> @common_options(disable_options=["format"])
    >>> def mycommand(abc, xyz):
    >>>     ...

    to disable use of `--format`
    """

    disable_opts = kwargs.get("disable_options", [])

    def decorate(f, **kwargs):
        """
        Work of actually decorating a function -- wrapped in here because we
        want to dispatch depending on how `common_options` is invoked
        """
        f = version_option(f)
        f = debug_option(f)
        f = verbose_option(f)
        f = click.help_option("-h", "--help")(f)

        # if the format option is being allowed, it needs to be applied to `f`
        if "format" not in disable_opts:
            f = format_option(f)

        # if the --map-http-status option is being allowed, ...
        if "map_http_status" not in disable_opts:
            f = map_http_status_option(f)

        return f

    return detect_and_decorate(decorate, args, kwargs)


def endpoint_id_arg(*args, **kwargs):
    """
    This is the `ENDPOINT_ID` argument consumed by many Transfer endpoint
    related operations. It accepts alternate metavars for cases when another
    name is desirable (e.x. `SHARE_ID`, `HOST_ENDPOINT_ID`), but can also be
    applied as a direct decorator if no specialized metavar is being passed.

    Usage:

    >>> @endpoint_id_arg
    >>> def command_func(endpoint_id):
    >>>     ...

    or

    >>> @endpoint_id_arg(metavar='HOST_ENDPOINT_ID')
    >>> def command_func(endpoint_id):
    >>>     ...
    """

    def decorate(f, **kwargs):
        """
        Work of actually decorating a function -- wrapped in here because we
        want to dispatch depending on how this is invoked
        """
        metavar = kwargs.get("metavar", "ENDPOINT_ID")
        f = click.argument("endpoint_id", metavar=metavar, type=click.UUID)(f)
        return f

    return detect_and_decorate(decorate, args, kwargs)


def endpoint_create_and_update_params(*args, **kwargs):
    """
    Collection of options consumed by Transfer endpoint create and update
    operations -- accepts toggle regarding create vs. update that makes
    display_name required vs. optional.

    Usage:

    >>> @endpoint_create_and_update_params(create=True)
    >>> def command_func(display_name, description, info_link, contact_info,
    >>>                  contact_email, organization, department, keywords,
    >>>                  public, location, disable_verify, myproxy_dn,
    >>>                  myproxy_server, oauth_server, force_encryption,
    >>>                  default_directory, subscription_id, network_use,
    >>>                  max_concurrency, preferred_concurrency,
    >>>                  max_parallelism, preferred_parallelism):
    >>>     ...
    """

    def inner_decorator(f, create=False):
        update_help_prefix = (not create and "New ") or ""

        # display name is required for create, not update
        if create:
            f = click.argument("display_name")(f)
        else:
            f = click.option(
                "--display-name", help=(update_help_prefix + "Name for the endpoint")
            )(f)

        # Options available to any endpoint
        f = click.option(
            "--description", help=(update_help_prefix + "Description for the endpoint")
        )(f)
        f = click.option(
            "--info-link",
            help=(update_help_prefix + "Link for Info about the endpoint"),
        )(f)
        f = click.option(
            "--contact-info",
            help=(update_help_prefix + "Contact Info for the endpoint"),
        )(f)
        f = click.option(
            "--contact-email",
            help=(update_help_prefix + "Contact Email for the endpoint"),
        )(f)
        f = click.option(
            "--organization",
            help=(update_help_prefix + "Organization for the endpoint"),
        )(f)
        f = click.option(
            "--department",
            help=(update_help_prefix + "Department which operates the endpoint"),
        )(f)
        f = click.option(
            "--keywords",
            help=(
                update_help_prefix
                + "Comma separated list of keywords to help searches "
                "for the endpoint"
            ),
        )(f)
        f = click.option("--default-directory", help=("Set the default directory"))(f)
        f = click.option(
            "--no-default-directory",
            is_flag=True,
            flag_value=True,
            default=None,
            help=("Unset any default directory on the endpoint"),
        )(f)
        f = click.option(
            "--force-encryption/--no-force-encryption",
            default=None,
            help=("(Un)Force the endpoint to encrypt transfers"),
        )(f)
        f = click.option(
            "--disable-verify/--no-disable-verify",
            is_flag=True,
            help="(Un)Set the endpoint to ignore checksum verification",
        )(f)

        # GCS only options
        f = click.option(
            "--public/--private",
            "public",
            default=None,
            help=(
                "Set the endpoint to be public or private "
                "(Globus Connect Server only)"
            ),
        )(f)
        f = click.option(
            "--myproxy-dn",
            help=("Set the MyProxy Server DN (Globus Connect Server only)"),
        )(f)
        f = click.option(
            "--myproxy-server",
            help="Set the MyProxy Server URI (Globus Connect Server only)",
        )(f)
        f = click.option(
            "--oauth-server",
            help=("Set the OAuth Server URI (Globus Connect Server only)"),
        )(f)
        f = click.option(
            "--location",
            type=LocationType(),
            default=None,
            help="Manually set the endpoint's latitude and longitude "
            "(Globus Connect Server only)",
        )(f)

        # Managed Endpoint options
        f = click.option(
            "--managed",
            "managed",
            is_flag=True,
            flag_value=True,
            default=None,
            help=(
                "Set the endpoint as a managed endpoint. Requires the "
                "user to be a subscription manager. If the user has "
                "multiple subscription IDs, --subscription-id must be used "
                "instead"
            ),
        )(f)
        f = click.option(
            "--no-managed",
            "managed",
            is_flag=True,
            flag_value=False,
            default=None,
            help=(
                "Unset the endpoint as a managed endpoint. "
                "Does not require the user to be a subscription manager. "
                "Mutually exclusive with --subscription-id"
            ),
        )(f)
        f = click.option(
            "--subscription-id",
            type=click.UUID,
            default=None,
            help=(
                "Set the endpoint as a managed endpoint with the given "
                "subscription ID. Mutually exclusive with "
                "--no-managed"
            ),
        )(f)
        f = click.option(
            "--network-use",
            default=None,
            type=click.Choice(["normal", "minimal", "aggressive", "custom"]),
            help=(
                "Set the endpoint's network use level. If using custom, "
                "the endpoint's max and preferred concurrency and "
                "parallelism must be set "
                "(Managed endpoints only) (Globus Connect Server only)"
            ),
        )(f)
        f = click.option(
            "--max-concurrency",
            type=int,
            default=None,
            help=(
                "Set the endpoint's max concurrency; "
                "requires --network-use=custom "
                "(Managed endpoints only) (Globus Connect Server only)"
            ),
        )(f)
        f = click.option(
            "--preferred-concurrency",
            type=int,
            default=None,
            help=(
                "Set the endpoint's preferred concurrency; "
                "requires --network-use=custom "
                "(Managed endpoints only) (Globus Connect Server only)"
            ),
        )(f)
        f = click.option(
            "--max-parallelism",
            type=int,
            default=None,
            help=(
                "Set the endpoint's max parallelism; "
                "requires --network-use=custom "
                "(Managed endpoints only) (Globus Connect Server only)"
            ),
        )(f)
        f = click.option(
            "--preferred-parallelism",
            type=int,
            default=None,
            help=(
                "Set the endpoint's preferred parallelism; "
                "requires --network-use=custom "
                "(Managed endpoints only) (Globus Connect Server only)"
            ),
        )(f)

        return f

    return detect_and_decorate(inner_decorator, args, kwargs)


def validate_endpoint_create_and_update_params(endpoint_type, managed, params):
    """
    Given an endpoint type of "shared" "server" or "personal" and option values
    Confirms the option values are valid for the given endpoint
    """
    # options only allowed for GCS endpoints
    if endpoint_type != "server":
        # catch params with two option flags
        if params["public"] is False:
            raise click.UsageError(
                "Option --private only allowed for Globus Connect Server endpoints"
            )
        # catch any params only usable with GCS
        for option in [
            "public",
            "myproxy_dn",
            "myproxy_server",
            "oauth_server",
            "location",
            "network_use",
            "max_concurrency",
            "preferred_concurrency",
            "max_parallelism",
            "preferred_parallelism",
        ]:
            if params[option] is not None:
                raise click.UsageError(
                    (
                        "Option --{} can only be used with Globus Connect Server "
                        "endpoints".format(option.replace("_", "-"))
                    )
                )

    # if the endpoint was not previously managed, and is not being passed
    # a subscription id, it cannot use managed endpoint only fields
    if (not managed) and not (params["subscription_id"] or params["managed"]):
        for option in [
            "network_use",
            "max_concurrency",
            "preferred_concurrency",
            "max_parallelism",
            "preferred_parallelism",
        ]:
            if params[option] is not None:
                raise click.UsageError(
                    (
                        "Option --{} can only be used with managed "
                        "endpoints".format(option.replace("_", "-"))
                    )
                )

    # because the Transfer service doesn't do network use level updates in a
    # patchy way, *both* endpoint `POST`s *and* `PUT`s must either use
    # - `network_use='custom'` with *every* other parameter specified (which
    #   is validated by the service), or
    # - a preset/absent `network_use` with *no* other parameter specified
    #   (which is *not* validated by the service; in this case, Transfer will
    #   accept but ignore the others parameters if given, leading to user
    #   confusion if we don't do this validation check)
    custom_network_use_params = (
        "max_concurrency",
        "preferred_concurrency",
        "max_parallelism",
        "preferred_parallelism",
    )
    if params["network_use"] != "custom":
        for option in custom_network_use_params:
            if params[option] is not None:
                raise click.UsageError(
                    "The {} options require you use --network-use=custom.".format(
                        "/".join(
                            "--" + option.replace("_", "-")
                            for option in custom_network_use_params
                        )
                    )
                )

    # make sure --(no-)managed and --subscription-id are mutually exclusive
    # if --managed given pass DEFAULT as the subscription_id
    # if --no-managed given, pass None
    managed_flag = params.get("managed")
    if managed_flag is not None:
        params.pop("managed")
        if managed_flag:
            params["subscription_id"] = params.get("subscription_id") or "DEFAULT"
        else:
            if params.get("subscription_id"):
                raise click.UsageError(
                    "Cannot specify --subscription-id and "
                    "use the --no-managed option."
                )
            params["subscription_id"] = EXPLICIT_NULL

    # make sure --no-default-directory are mutually exclusive
    # if --no-managed given, pass an EXPLICIT_NULL as the default directory
    if params.get("no_default_directory"):

        if params.get("default_directory"):
            raise click.UsageError(
                "--no-default-directory and --default-directory are mutually "
                "exclusive."
            )
        else:
            params["default_directory"] = EXPLICIT_NULL
            params.pop("no_default_directory")


def task_id_arg(*args, **kwargs):
    """
    This is the `TASK_ID` argument consumed by many Transfer Task operations.
    It accept a toggle on whether or not it is required

    Usage:

    >>> @task_id_option
    >>> def command_func(task_id):
    >>>     ...

    or

    >>> @task_id_option(required=False)
    >>> def command_func(task_id):
    >>>     ...

    By default, the task ID is made required; pass `required=False` to the
    decorator arguments to make it optional.
    """

    def inner_decorator(f, required=True):
        f = click.argument("TASK_ID", required=required)(f)
        return f

    return detect_and_decorate(inner_decorator, args, kwargs)


def task_submission_options(f):
    """
    Options shared by both transfer and delete task submission
    """

    def notify_opt_callback(ctx, param, value):
        """
        Parse --notify
        - "" is the same as "off"
        - parse by lowercase, comma-split, strip spaces
        - "off,x" is invalid for any x
        - "on,x" is valid for any valid x (other than "off")
        - "failed", "succeeded", "inactive" are normal vals

        In code, produces True, False, or a set
        """
        # if no value was set, don't set any explicit options
        # the API default is "everything on"
        if value is None:
            return {}

        value = value.lower()
        value = [x.strip() for x in value.split(",")]
        # [""] is what you'll get if value is "" to start with
        # special-case it into "off", which helps avoid surprising scripts
        # which take a notification settings as inputs and build --notify
        if value == [""]:
            value = ["off"]

        off = "off" in value
        on = "on" in value
        # set-ize it -- duplicates are fine
        vals = set([x for x in value if x not in ("off", "on")])

        if (vals or on) and off:
            raise click.UsageError('--notify cannot accept "off" and another value')

        allowed_vals = set(("on", "succeeded", "failed", "inactive"))
        if not vals <= allowed_vals:
            raise click.UsageError(
                "--notify received at least one invalid value among {}".format(
                    list(vals)
                )
            )

        # return the notification options to send!
        # on means don't set anything (default)
        if on:
            return {}
        # off means turn off everything
        if off:
            return {
                "notify_on_succeeded": False,
                "notify_on_failed": False,
                "notify_on_inactive": False,
            }
        # otherwise, return the exact set of values seen
        else:
            return {
                "notify_on_succeeded": "succeeded" in vals,
                "notify_on_failed": "failed" in vals,
                "notify_on_inactive": "inactive" in vals,
            }

    def format_deadline_callback(ctx, param, value):
        if not value:
            return None
        return value.strftime("%Y-%m-%d %H:%M:%S")

    f = click.option(
        "--dry-run",
        is_flag=True,
        help="Don't actually submit the task, print submission data instead",
    )(f)
    f = click.option(
        "--notify",
        callback=notify_opt_callback,
        help=(
            "Comma separated list of task events which notify by email. "
            "'on' and 'off' may be used to enable or disable notifications "
            "for all event types. Otherwise, use 'succeeded', 'failed', or "
            "'inactive'"
        ),
    )(f)
    f = click.option(
        "--submission-id",
        help=(
            "Task submission ID, as generated by `globus task "
            "generate-submission-id`. Used for safe resubmission in the "
            "presence of network failures."
        ),
    )(f)
    f = click.option("--label", default=None, help="Set a label for this task.")(f)
    f = click.option(
        "--deadline",
        default=None,
        type=click.DateTime(),
        callback=format_deadline_callback,
        help="Set a deadline for this to be canceled if not completed by.",
    )(f)
    f = click.option(
        "--skip-activation-check",
        is_flag=True,
        help="Submit the task even if the endpoint(s) aren't currently activated.",
    )(f)

    return f


def delete_and_rm_options(*args, **kwargs):
    """
    Options which apply both to `globus delete` and `globus rm`
    """

    def inner_decorator(f, supports_batch=True, default_enable_globs=False):
        f = click.option(
            "--recursive", "-r", is_flag=True, help="Recursively delete dirs"
        )(f)
        f = click.option(
            "--ignore-missing",
            "-f",
            is_flag=True,
            help="Don't throw errors if the file or dir is absent",
        )(f)
        f = click.option(
            "--star-silent",
            "--unsafe",
            "star_silent",
            is_flag=True,
            help=(
                'Don\'t prompt when the trailing character is a "*".'
                + (" Implicit in --batch" if supports_batch else "")
            ),
        )(f)
        f = click.option(
            "--enable-globs/--no-enable-globs",
            is_flag=True,
            default=default_enable_globs,
            show_default=True,
            help=(
                "Enable expansion of *, ?, and [ ] characters in the last "
                "component of file paths, unless they are escaped with "
                "a preceeding backslash, \\"
            ),
        )(f)
        if supports_batch:
            f = click.option(
                "--batch",
                is_flag=True,
                help=(
                    "Accept a batch of paths on stdin (i.e. run in "
                    "batchmode). Uses ENDPOINT_ID as passed on the "
                    "commandline. Any commandline PATH given will be used "
                    "as a prefix to all paths given"
                ),
            )(f)
        return f

    return detect_and_decorate(inner_decorator, args, kwargs)


def synchronous_task_wait_options(f):
    def polling_interval_callback(ctx, param, value):
        if not value:
            return None

        if value < 1:
            raise click.UsageError(
                "--polling-interval={0} was less than minimum of {1}".format(value, 1)
            )

        return value

    def exit_code_callback(ctx, param, value):
        if not value:
            return None

        exit_stat_set = [0, 1] + list(range(50, 100))
        if value not in exit_stat_set:
            raise click.UsageError("--timeout-exit-code must have a value in 0,1,50-99")

        return value

    f = click.option(
        "--timeout",
        type=int,
        metavar="N",
        help=(
            "Wait N seconds. If the Task does not terminate by "
            "then, or terminates with an unsuccessful status, "
            "exit with status 1"
        ),
    )(f)
    f = click.option(
        "--polling-interval",
        default=1,
        type=int,
        show_default=True,
        callback=polling_interval_callback,
        help="Number of seconds between Task status checks.",
    )(f)
    f = click.option(
        "--heartbeat",
        "-H",
        is_flag=True,
        help=(
            'Every polling interval, print "." to stdout to '
            "indicate that task wait is till active"
        ),
    )(f)
    f = click.option(
        "--timeout-exit-code",
        type=int,
        default=1,
        show_default=True,
        callback=exit_code_callback,
        help=(
            "If the task times out, exit with this status code. Must have "
            "a value in 0,1,50-99"
        ),
    )(f)
    f = click.option("--meow", is_flag=True, hidden=True)(f)
    return f


def role_id_arg(f):
    """
    Unmodifiable `ROLE_ID` argument for Transfer Endpoint Role management.
    """
    return click.argument("role_id")(f)


def server_id_arg(f):
    """
    Unmodifiable `SERVER_ID` argument for Transfer Endpoint Server management.
    """
    return click.argument("server_id")(f)


def server_add_and_update_opts(*args, **kwargs):
    """
    shared collection of options for `globus transfer endpoint server add` and
    `globus transfer endpoint server update`.
    Accepts a toggle to know if it's being used as `add` or `update`.

    usage:

    >>> @server_add_and_update_opts
    >>> def command_func(subject, port, scheme, hostname):
    >>>     ...

    or

    >>> @server_add_and_update_opts(add=True)
    >>> def command_func(subject, port, scheme, hostname):
    >>>     ...
    """

    def port_range_callback(ctx, param, value):
        if not value:
            return None

        value = value.lower().strip()
        if value == "unspecified":
            return None, None
        if value == "unrestricted":
            return 1024, 65535

        try:
            lower, upper = map(int, value.split("-"))
        except ValueError:  # too many/few values from split or non-integer(s)
            raise click.BadParameter(
                "must specify as 'unspecified', "
                "'unrestricted', or as range separated "
                "by a hyphen (e.g. '50000-51000')"
            )
        if not 1024 <= lower <= 65535 or not 1024 <= upper <= 65535:
            raise click.BadParameter("must be within the 1024-65535 range")

        return (lower, upper) if lower <= upper else (upper, lower)

    def inner_decorator(f, add=False):
        f = click.option("--hostname", required=add, help="Server Hostname.")(f)

        default_scheme = "gsiftp" if add else None
        f = click.option(
            "--scheme",
            help="Scheme for the Server.",
            type=click.Choice(("gsiftp", "ftp"), case_sensitive=False),
            default=default_scheme,
            show_default=add,
        )(f)

        default_port = 2811 if add else None
        f = click.option(
            "--port",
            help="Port for Globus control channel connections.",
            type=int,
            default=default_port,
            show_default=add,
        )(f)

        f = click.option(
            "--subject",
            help=(
                "Subject of the X509 Certificate of the server. When "
                "unspecified, the CN must match the server hostname."
            ),
        )(f)

        for adjective, our_preposition, their_preposition in [
            ("incoming", "to", "from"),
            ("outgoing", "from", "to"),
        ]:
            f = click.option(
                "--{}-data-ports".format(adjective),
                callback=port_range_callback,
                help="Indicate to firewall administrators at other sites how to "
                "allow {} traffic {} this server {} their own. Specify as "
                "either 'unspecified', 'unrestricted', or as range of "
                "ports separated by a hyphen (e.g. '50000-51000') within "
                "the 1024-65535 range.".format(
                    adjective, our_preposition, their_preposition
                ),
            )(f)

        return f

    return detect_and_decorate(inner_decorator, args, kwargs)


def security_principal_opts(*args, **kwargs):
    def preprocess_security_principals(f):
        @functools.wraps(f)
        def decorator(*args, **kwargs):
            identity = kwargs.pop("identity", None)
            group = kwargs.pop("group", None)
            provision_identity = kwargs.pop("provision_identity", None)

            has_identity = identity or provision_identity

            if identity and provision_identity:
                raise click.UsageError(
                    "Only one of --identity or --provision-identity allowed"
                )
            if kwargs.get("principal") is not None:
                if has_identity or group:
                    raise click.UsageError("You may only pass one security principal")
            else:
                if has_identity and group:
                    raise click.UsageError(
                        (
                            "You have passed both an identity and a group. "
                            "Please only pass one principal type"
                        )
                    )
                elif not has_identity and not group:
                    raise click.UsageError(
                        (
                            "You must provide at least one principal "
                            "(identity, group, etc.)"
                        )
                    )

                if identity:
                    kwargs["principal"] = ("identity", identity)
                elif provision_identity:
                    kwargs["principal"] = ("provision-identity", provision_identity)
                else:
                    kwargs["principal"] = ("group", group)

            return f(*args, **kwargs)

        return decorator

    def inner_decorator(
        f, allow_anonymous=False, allow_all_authenticated=False, allow_provision=False
    ):

        # order matters here -- the preprocessor must run after option
        # application, so it has to be applied first
        if isinstance(f, click.Command):
            # if we're decorating a command, put the preprocessor on its
            # callback, not on `f` itself
            f.callback = preprocess_security_principals(f.callback)
        else:
            # otherwise, we're applying to a function, but other decorators may
            # have been applied to give it params
            # so, copy __click_params__ to preserve those parameters
            oldfun = f
            f = preprocess_security_principals(f)
            f.__click_params__ = getattr(oldfun, "__click_params__", [])

        f = click.option(
            "--identity",
            metavar="IDENTITY_ID_OR_NAME",
            help="Identity to use as a security principal",
        )(f)
        f = click.option(
            "--group", metavar="GROUP_ID", help="Group to use as a security principal"
        )(f)

        if allow_anonymous:
            f = click.option(
                "--anonymous",
                "principal",
                flag_value=("anonymous", ""),
                help=(
                    "Allow anyone access, even without logging in "
                    "(treated as a security principal)"
                ),
            )(f)
        if allow_all_authenticated:
            f = click.option(
                "--all-authenticated",
                "principal",
                flag_value=("all_authenticated_users", ""),
                help=(
                    "Allow anyone access, as long as they login"
                    "(treated as a security principal)"
                ),
            )(f)

        if allow_provision:
            f = click.option(
                "--provision-identity",
                metavar="IDENTITY_USERNAME",
                help="Identity username to use as a security principal. "
                "Identity will be provisioned if it does not exist.",
            )(f)

        return f

    return detect_and_decorate(inner_decorator, args, kwargs)


def no_local_server_option(f):
    """
    Option for commands that start auth flows and might need to disable
    the default local server behavior
    """
    return click.option(
        "--no-local-server",
        is_flag=True,
        help=(
            "Manual authorization by copying and pasting an auth code. "
            "This option is implied if the CLI detects you are using a "
            "remote connection."
        ),
    )(f)
