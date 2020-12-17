from globus_cli.parsing import (
    command,
    endpoint_create_and_update_params,
    endpoint_id_arg,
    validate_endpoint_create_and_update_params,
)
from globus_cli.safeio import FORMAT_TEXT_RAW, formatted_print
from globus_cli.services.transfer import assemble_generic_doc, get_client


@command("update")
@endpoint_id_arg
@endpoint_create_and_update_params(create=False)
def endpoint_update(**kwargs):
    """Update attributes of an endpoint"""
    # validate params. Requires a get call to check the endpoint type
    client = get_client()
    endpoint_id = kwargs.pop("endpoint_id")
    get_res = client.get_endpoint(endpoint_id)

    if get_res["host_endpoint_id"]:
        endpoint_type = "shared"
    elif get_res["is_globus_connect"]:
        endpoint_type = "personal"
    elif get_res["s3_url"]:
        endpoint_type = "s3"
    else:
        endpoint_type = "server"
    validate_endpoint_create_and_update_params(
        endpoint_type, get_res["subscription_id"], kwargs
    )

    # make the update
    ep_doc = assemble_generic_doc("endpoint", **kwargs)
    res = client.update_endpoint(endpoint_id, ep_doc)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
