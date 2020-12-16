import logging.config
import os

import globus_sdk
from configobj import ConfigObj

__all__ = [
    # option name constants
    "OUTPUT_FORMAT_OPTNAME",
    "MYPROXY_USERNAME_OPTNAME",
    "AUTH_RT_OPTNAME",
    "AUTH_AT_OPTNAME",
    "AUTH_AT_EXPIRES_OPTNAME",
    "TRANSFER_RT_OPTNAME",
    "TRANSFER_AT_OPTNAME",
    "AUTH_AT_EXPIRES_OPTNAME",
    "CLIENT_ID_OPTNAME",
    "CLIENT_SECRET_OPTNAME",
    "GLOBUS_ENV",
    "internal_native_client",
    "internal_auth_client",
    "get_output_format",
    "get_auth_tokens",
    "get_transfer_tokens",
    "get_config_obj",
    "write_option",
    "remove_option",
    "lookup_option",
]


# constants for use whenever we need to do things using
# instance clients from the CLI Native App Template
# primarily accessed via `internal_auth_client()`
CLIENT_ID_OPTNAME = "client_id"
CLIENT_SECRET_OPTNAME = "client_secret"
TEMPLATE_ID_OPTNAME = "template_id"
DEFAULT_TEMPLATE_ID = "95fdeba8-fac2-42bd-a357-e068d82ff78e"

# constants for global use
OUTPUT_FORMAT_OPTNAME = "output_format"
MYPROXY_USERNAME_OPTNAME = "default_myproxy_username"
AUTH_RT_OPTNAME = "auth_refresh_token"
AUTH_AT_OPTNAME = "auth_access_token"
AUTH_AT_EXPIRES_OPTNAME = "auth_access_token_expires"
TRANSFER_RT_OPTNAME = "transfer_refresh_token"
TRANSFER_AT_OPTNAME = "transfer_access_token"
TRANSFER_AT_EXPIRES_OPTNAME = "transfer_access_token_expires"

# get the environment from env var (not exported)
GLOBUS_ENV = os.environ.get("GLOBUS_SDK_ENVIRONMENT")

# if the env is set, rewrite the option names to have it as a prefix
if GLOBUS_ENV:
    AUTH_RT_OPTNAME = "{0}_auth_refresh_token".format(GLOBUS_ENV)
    AUTH_AT_OPTNAME = "{0}_auth_access_token".format(GLOBUS_ENV)
    AUTH_AT_EXPIRES_OPTNAME = "{0}_auth_access_token_expires".format(GLOBUS_ENV)
    TRANSFER_RT_OPTNAME = "{0}_transfer_refresh_token".format(GLOBUS_ENV)
    TRANSFER_AT_OPTNAME = "{0}_transfer_access_token".format(GLOBUS_ENV)
    TRANSFER_AT_EXPIRES_OPTNAME = "{0}_transfer_access_token_expires".format(GLOBUS_ENV)

    CLIENT_ID_OPTNAME = "{0}_client_id".format(GLOBUS_ENV)
    CLIENT_SECRET_OPTNAME = "{0}_client_secret".format(GLOBUS_ENV)
    TEMPLATE_ID_OPTNAME = "{0}_template_id".format(GLOBUS_ENV)
    DEFAULT_TEMPLATE_ID = {
        "sandbox": "33b6a241-bce4-4359-9c6d-09f88b3c9eef",
        "integration": "e0c31fd1-663b-44e1-840f-f4304bb9ee7a",
        "test": "0ebfd058-452f-40c3-babf-5a6b16a7b337",
        "staging": "3029c3cb-c8d9-4f2b-979c-c53330aa7327",
        "preview": "b2867dbb-0846-4579-8486-dc70763d700b",
    }.get(GLOBUS_ENV, DEFAULT_TEMPLATE_ID)


def get_config_obj(system=False, file_error=False):
    if system:
        path = "/etc/globus.cfg"
    else:
        path = os.path.expanduser("~/.globus.cfg")

    conf = ConfigObj(path, encoding="utf-8", file_error=file_error)

    # delete any old whomai values in the cli section
    for key in conf.get("cli", {}):
        if "whoami_identity_" in key:
            del conf["cli"][key]
            conf.write()

    return conf


def lookup_option(option, section="cli", environment=None):
    conf = get_config_obj()
    try:
        if environment:
            return conf["environment " + environment][option]
        else:
            return conf[section][option]
    except KeyError:
        return None


def remove_option(option, section="cli", system=False):
    conf = get_config_obj(system=system)

    # if there's no section for the option we're removing, just return None
    try:
        section = conf[section]
    except KeyError:
        return None

    try:
        opt_val = section[option]

        # remove value and flush to disk
        del section[option]
        conf.write()
    except KeyError:
        opt_val = None

    # return the just-deleted value
    return opt_val


def write_option(option, value, section="cli", system=False):
    """
    Write an option to disk -- doesn't handle config reloading
    """
    # deny rwx to Group and World -- don't bother storing the returned old mask
    # value, since we'll never restore it in the CLI anyway
    # do this on every call to ensure that we're always consistent about it
    os.umask(0o077)

    # FIXME: DRY violation with config_commands.helpers
    conf = get_config_obj(system=system)

    # add the section if absent
    if section not in conf:
        conf[section] = {}

    conf[section][option] = value
    conf.write()


def get_output_format():
    return lookup_option(OUTPUT_FORMAT_OPTNAME)


def get_auth_tokens():
    expires = lookup_option(AUTH_AT_EXPIRES_OPTNAME)
    if expires is not None:
        expires = int(expires)

    return {
        "refresh_token": lookup_option(AUTH_RT_OPTNAME),
        "access_token": lookup_option(AUTH_AT_OPTNAME),
        "access_token_expires": expires,
    }


def set_auth_tokens(access_token, refresh_token, expires_at):
    write_option(AUTH_AT_OPTNAME, access_token)
    write_option(AUTH_RT_OPTNAME, refresh_token)
    write_option(AUTH_AT_EXPIRES_OPTNAME, expires_at)


def get_transfer_tokens():
    expires = lookup_option(TRANSFER_AT_EXPIRES_OPTNAME)
    if expires is not None:
        expires = int(expires)

    return {
        "refresh_token": lookup_option(TRANSFER_RT_OPTNAME),
        "access_token": lookup_option(TRANSFER_AT_OPTNAME),
        "access_token_expires": expires,
    }


def set_transfer_tokens(access_token, refresh_token, expires_at):
    write_option(TRANSFER_AT_OPTNAME, access_token)
    write_option(TRANSFER_RT_OPTNAME, refresh_token)
    write_option(TRANSFER_AT_EXPIRES_OPTNAME, expires_at)


def internal_native_client():
    template_id = lookup_option(TEMPLATE_ID_OPTNAME) or DEFAULT_TEMPLATE_ID
    return globus_sdk.NativeAppAuthClient(template_id)


def internal_auth_client(requires_instance=False, force_new_client=False):
    """
    Looks up the values for this CLI's Instance Client in config

    If none exists and requires_instance is True or force_new_client is True,
    registers a new Instance Client with Globus Auth

    If none exists and requires_instance is false, defaults to a Native Client
    for backwards compatibility

    Returns either a NativeAppAuthClient or a ConfidentialAppAuthClient
    """
    client_id = lookup_option(CLIENT_ID_OPTNAME)
    client_secret = lookup_option(CLIENT_SECRET_OPTNAME)
    template_id = lookup_option(TEMPLATE_ID_OPTNAME) or DEFAULT_TEMPLATE_ID
    template_client = internal_native_client()
    existing = client_id and client_secret

    # if we are forcing a new client, delete any existing client
    if force_new_client and existing:
        existing_client = globus_sdk.ConfidentialAppAuthClient(client_id, client_secret)
        try:
            existing_client.delete("/v2/api/clients/{}".format(client_id))

        # if the client secret has been invalidated or the client has
        # already been removed, we continue on
        except globus_sdk.exc.AuthAPIError:
            pass

    # if we require a new client to be made
    if force_new_client or (requires_instance and not existing):
        # register a new instance client with auth
        body = {"client": {"template_id": template_id, "name": "Globus CLI"}}
        res = template_client.post("/v2/api/clients", json_body=body)

        # get values and write to config
        credential_data = res["included"]["client_credential"]
        client_id = credential_data["client"]
        client_secret = credential_data["secret"]
        write_option(CLIENT_ID_OPTNAME, client_id)
        write_option(CLIENT_SECRET_OPTNAME, client_secret)

        return globus_sdk.ConfidentialAppAuthClient(
            client_id, client_secret, app_name="Globus CLI"
        )

    # if we already have a client, just return it
    elif existing:
        return globus_sdk.ConfidentialAppAuthClient(
            client_id, client_secret, app_name="Globus CLI"
        )

    # fall-back to a native client to not break old logins
    # TOOD: eventually remove this behavior
    else:
        return template_client


def setup_logging(level="DEBUG"):
    conf = {
        "version": 1,
        "formatters": {
            "basic": {"format": "[%(levelname)s] %(name)s::%(funcName)s() %(message)s"}
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "basic",
            }
        },
        "loggers": {"globus_sdk": {"level": level, "handlers": ["console"]}},
    }

    logging.config.dictConfig(conf)
