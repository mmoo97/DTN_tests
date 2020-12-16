import re

from globus_sdk import AuthClient, RefreshTokenAuthorizer

from globus_cli import version
from globus_cli.config import get_auth_tokens, internal_auth_client, set_auth_tokens

# what qualifies as a valid Identity Name?
_IDENTITY_NAME_REGEX = r"^[a-zA-Z0-9]+.*@[a-zA-z0-9-]+\..*[a-zA-Z]+$"


def _update_tokens(token_response):
    tokens = token_response.by_resource_server["auth.globus.org"]
    set_auth_tokens(
        tokens["access_token"], tokens["refresh_token"], tokens["expires_at_seconds"]
    )


def is_valid_identity_name(identity_name):
    """
    Check if a string is a valid identity name.
    Does not do any preprocessing of the identity name, so you must do so
    before invocation.
    """
    if re.match(_IDENTITY_NAME_REGEX, identity_name) is None:
        return False
    else:
        return True


def get_auth_client():
    tokens = get_auth_tokens()
    authorizer = None

    # if there's a refresh token, use it to build the authorizer
    if tokens["refresh_token"] is not None:
        authorizer = RefreshTokenAuthorizer(
            tokens["refresh_token"],
            internal_auth_client(),
            tokens["access_token"],
            tokens["access_token_expires"],
            on_refresh=_update_tokens,
        )

    client = AuthClient(authorizer=authorizer, app_name=version.app_name)
    return client


def _lookup_identity_field(id_name=None, id_id=None, field="id", provision=False):
    assert (id_name or id_id) and not (id_name and id_id)
    client = get_auth_client()

    kw = dict(provision=provision)
    if id_name:
        kw.update({"usernames": id_name})
    else:
        kw.update({"ids": id_id})

    try:
        return client.get_identities(**kw)["identities"][0][field]
    except (IndexError, KeyError):
        # IndexError: identity does not exist and wasn't provisioned
        # KeyError: `field` does not exist for the requested identity
        return None


def maybe_lookup_identity_id(identity_name, provision=False):
    if is_valid_identity_name(identity_name):
        return _lookup_identity_field(id_name=identity_name, provision=provision)
    else:
        return identity_name


def lookup_identity_name(identity_id):
    return _lookup_identity_field(id_id=identity_id, field="username")
