import globus_sdk
import sys
import argparse
from time import sleep


def get_args():
    parser = argparse.ArgumentParser(description='Capture Globus transfer speeds between two endpoints.')
    parser.add_argument('client', type=str, help='The Client ID of the account testing the transfers')
    parser.add_argument('src_ep_id', type=str, help='The Endpoint ID of the source endpoint.')
    parser.add_argument('dest_ep_id', type=str, help='The Endpoint ID of the destination endpoint.')
    parser.add_argument('src_dir', type=str, help='The desired directory from the source endpoint.')
    parser.add_argument('dest_dir', type=str, help='The desired directory from the destination endpoint.')

    return parser.parse_args()


def get_token(client_id):
    ''' Code to gt access token'''
    client = globus_sdk.NativeAppAuthClient(client_id)
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

    return globus_sdk.RefreshTokenAuthorizer(
        transfer_rt, client, access_token=transfer_at, expires_at=expires_at_s)


def transfer_data(tc, src_id, dest_id, src_dir, dest_dir):

    tdata = globus_sdk.TransferData(tc, src_id,
                                     dest_id,
                                     label="Dataset Test",
                                    sync_level=None, verify="checksum")

    tdata.add_item(src_dir, dest_dir, recursive=True)

    transfer_result = tc.submit_transfer(tdata)
    print("task_id =", transfer_result["task_id"])

    task = tc.get_task(transfer_result["task_id"])
    while True:
        if task["status"] == "SUCCEEDED":
            print("Task Status: " + task["status"])
            print("Effective Speed: " + str(round(task["effective_bytes_per_second"]/(1024*1024), 2)) + " MB/s")
            break
        else:

            # sys.stdout.write("\rDoing thing %i" % i)
            # sys.stdout.flush()
            sys.stdout.write("\rTask Status: %s\n" % task["status"])
            sys.stdout.write("\rMB Transferred: %s MB\n" % str(round(task["bytes_transferred"]/1000000, 2)))
            sys.stdout.flush()
            sleep(3)




if __name__ == '__main__':
    args = get_args()
    authorizer = get_token(args.client)
    tc = globus_sdk.TransferClient(authorizer=authorizer)

    transfer_data(tc, args.src_ep_id, args.dest_ep_id, args.src_dir, args.dest_dir)

    # print("My Endpoints:")
    # for ep in tc.endpoint_search(filter_scope="recently-used"):
    #     print("[{}] {}".format(ep["id"], ep["display_name"]))
    #
    # print("\n")
    # for task in tc.task_list():
    #     print("Task({}): {} -> {}".format(
    #         task["task_id"], task["source_endpoint"],
    #         task["destination_endpoint"]))

