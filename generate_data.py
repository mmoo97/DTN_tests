import globus_sdk
import vars

''' Code to get access token'''
client = globus_sdk.NativeAppAuthClient(vars.CLIENT_ID)
client.oauth2_start_flow(refresh_tokens=True)

print('Please go to this URL and login: {0}'
      .format(client.oauth2_get_authorize_url()))

get_input = getattr(__builtins__, 'raw_input', input)
auth_code = get_input('Please enter the code here: ').strip()
token_response = client.oauth2_exchange_code_for_tokens(auth_code)

globus_auth_data = token_response.by_resource_server['auth.globus.org']

globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']

# the refresh token and access token, often abbr. as RT and AT
transfer_rt = globus_transfer_data['refresh_token']
transfer_at = globus_transfer_data['access_token']
expires_at_s = globus_transfer_data['expires_at_seconds']

# Now we've got the data we need, but what do we do?
# That "GlobusAuthorizer" from before is about to come to the rescue

authorizer = globus_sdk.RefreshTokenAuthorizer(
    transfer_rt, client, access_token=transfer_at, expires_at=expires_at_s)

tc = globus_sdk.TransferClient(authorizer=authorizer)

# high level interface; provides iterators for list responses
print("My Endpoints:")
for ep in tc.endpoint_search(filter_scope="recently-used"):
    print("[{}] {}".format(ep["id"], ep["display_name"]))

print("\n")
for task in tc.task_list():
    print("Task({}): {} -> {}".format(
        task["task_id"], task["source_endpoint"],
        task["destination_endpoint"]))

tdata = globus_sdk.TransferData(tc, vars.source_endpoint_id_list[0],
                                 vars.destination_endpoint_id,
                                 label="Dataset Test",
                                sync_level=None, verify="checksum")
# tdata.add_item("/globus/datasets/ds04/", "/data/user/mmoo97/TEST_TRANSFER/",
#                 recursive=True)
# for item in tdata.items:
#     print(item)
tdata.add_item(vars.source_dirs, vars.dest_dir,
                recursive=True)
print(tdata.items())
# transfer_result = tc.submit_transfer(tdata)
# print("task_id =", transfer_result["task_id"])

# task = tc.get_task(transfer_result["task_id"])
task = tc.get_task("750a002a-0901-11eb-abd6-0213fe609573")
if task["status"] == "SUCCEEDED":
    print("Task Status: " + task["status"])
    print("Effective Speed: " + str(round(task["effective_bytes_per_second"]/(1024*1024), 2)) + " MB/s")
else:
    print("Task Status: " + task["status"])
    print("MB Transferred: " + str(round(task["bytes_transferred"]/1000000, 2)) + " MB")