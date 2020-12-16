import uuid

import click

from globus_cli.parsing import EXPLICIT_NULL, command, endpoint_id_arg
from globus_cli.safeio import FORMAT_TEXT_RAW, formatted_print
from globus_cli.services.transfer import get_client


class SubscriptionIdType(click.ParamType):
    def convert(self, value, param, ctx):
        if value is None or (ctx and ctx.resilient_parsing):
            return None
        if value.lower() == "null":
            return EXPLICIT_NULL
        try:
            uuid.UUID(value)
            return value
        except ValueError:
            self.fail("{} is not a valid Subscription ID".format(value), param, ctx)


@command("set-subscription-id", short_help="Set an endpoint's subscription")
@endpoint_id_arg
@click.argument("SUBSCRIPTION_ID", type=SubscriptionIdType())
def set_endpoint_subscription_id(**kwargs):
    """
    Set an endpoint's subscription ID.

    Unlike the '--managed' flag for 'globus endpoint update', this operation does not
    require you to be an admin of the endpoint. It is useful in cases where you are a
    subscription manager applying a subscription to an endpoint with a different admin.

    SUBSCRIPTION_ID should either be a valid subscription ID or 'null'.
    """
    # validate params. Requires a get call to check the endpoint type
    client = get_client()
    endpoint_id = kwargs.pop("endpoint_id")
    subscription_id = kwargs.pop("subscription_id")
    if subscription_id is EXPLICIT_NULL:
        subscription_id = None

    # make the update
    res = client.put(
        "/endpoint/{}/subscription".format(endpoint_id),
        {"subscription_id": subscription_id},
    )
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
