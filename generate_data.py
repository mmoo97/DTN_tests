import globus_sdk
import sys
import argparse
from time import sleep
import progressbar
import csv
from datetime import datetime


def get_args():
    parser = argparse.ArgumentParser(description='Capture Globus transfer speeds between two endpoints.')
    parser.add_argument('client', type=str, help='The Client ID of the account testing the transfers')
    parser.add_argument('src_ep_id', type=str, help='The Endpoint ID of the source endpoint.')
    parser.add_argument('dest_ep_id', type=str, help='The Endpoint ID of the destination endpoint.')
    parser.add_argument('src_dir', type=str, help='The desired directory from the source endpoint.')
    parser.add_argument('dest_dir', type=str, help='The desired directory from the destination endpoint.')
    parser.add_argument('-r, --refresh-token', dest='refresh_token', type=str,
                        help='The resource token for Globus Authentication.')

    return parser.parse_args()


def get_authorizer(client_id, **kwargs):
    """Code to gt access token"""
    client = globus_sdk.NativeAppAuthClient(client_id)
    refresh_token = kwargs.get('refresh_token')
    token_response = None

    if refresh_token is None:
        client.oauth2_start_flow(refresh_tokens=True)

        print('Please go to this URL and login: {0}'
              .format(client.oauth2_get_authorize_url()))

        get_input = getattr(__builtins__, 'raw_input', input)
        auth_code = get_input('Please enter the code here: ').strip()
        token_response = client.oauth2_exchange_code_for_tokens(auth_code)

        globus_auth_data = token_response.by_resource_server['auth.globus.org']
        globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']

        transfer_token = globus_transfer_data['access_token']
        print("\nTo avoid browser-based token authentication in the future, consider"
              " using the refresh token below by invoking the [-r] flag upon program initiation.")
        print("\tRefresh token:\t" + globus_transfer_data['refresh_token'] + "\n")

        return globus_sdk.AccessTokenAuthorizer(transfer_token)

    else:
        client.oauth2_start_flow(refresh_tokens=True)
        token_response = client.oauth2_refresh_token(refresh_token)
        globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']

        # the refresh token and access token, often abbr. as RT and AT
        transfer_rt = globus_transfer_data['refresh_token']
        transfer_at = globus_transfer_data['access_token']
        expires_at_s = globus_transfer_data['expires_at_seconds']

        return globus_sdk.RefreshTokenAuthorizer(
            transfer_rt, client, access_token=transfer_at, expires_at=expires_at_s)


def transfer_data(tc, src_id, dest_id, src_dir, dest_dir, output):

    tdata = globus_sdk.TransferData(tc, src_id,
                                     dest_id,
                                     label="{}".format(src_dir.split("/")[-1]),
                                    sync_level=None, verify="checksum")

    tdata.add_item(src_dir, dest_dir, recursive=True)

    transfer_result = tc.submit_transfer(tdata)
    bar = progressbar.ProgressBar(max_value=progressbar.UnknownLength)

    if output:
        print("\ntask_id =", transfer_result["task_id"])

    while True:
        task = tc.get_task(transfer_result["task_id"])

        if task["status"] == "SUCCEEDED":
            if output:
                bar.finish()
                print("Task Status: " + task["status"])
                print("Effective Speed: " + str(round(task["effective_bytes_per_second"]/(1024*1024), 2)) + " MB/s")

            return {"dataset": src_dir.split("/")[-1],
                    "start": task["request_time"],
                    "end": task["completion_time"],
                    # Todo: Make it so that the elapsed time can be created outside of the progress bar context.
                    "elapsed": str(bar.data()['time_elapsed']),
                    "speed": str(round(task["effective_bytes_per_second"]/(1024*1024), 2)),
                    "src_ep_id": src_id,
                    "dest_ep_id": dest_id,
                    "task_id": transfer_result["task_id"]}

        elif task["status"] == "ACTIVE":
            if output:
                # Todo: Add 'MB' to the end of progress bar output
                bar.update(round(task["bytes_transferred"]/1000000, 2))
                sleep(.5)

        else:
            if output:
                bar.finish()
                print("\rTask Status: %s\n" % task["status"])
            exit(-1)


def write_results(data_dict, filename):
    with open(filename, 'a+', newline='') as file:
        writer = csv.writer(file)
        count = 0
        read = csv.reader(file, delimiter=",")

        if file.tell() == 0:
            writer.writerow(["Dataset", "Start", "End", "Elapsed", "Speed", "Source EP ID", "Dest. EP ID", "Task ID"])

        writer.writerow([data_dict["dataset"],
                    data_dict["start"],
                    data_dict["end"],
                    data_dict["elapsed"],
                    data_dict["speed"],
                    data_dict["src_ep_id"],
                    data_dict["dest_ep_id"],
                    data_dict["task_id"]])


if __name__ == '__main__':
    args = get_args()
    authorizer = get_authorizer(args.client,
                                refresh_token=args.refresh_token)
    tc = globus_sdk.TransferClient(authorizer=authorizer)

    # Todo: Make it so that the elapsed time can be created outside of the progress bar context.
    # print(transfer_data(tc, args.src_ep_id, args.dest_ep_id, args.src_dir, args.dest_dir, True))

    # write_results(transfer_data(tc, args.src_ep_id, args.dest_ep_id, args.src_dir, args.dest_dir, True), "test.csv")

    data_sets = [1, 4, 6, 8, 10, 12, 14, 16]
    test_start = datetime.now().strftime("%m-%d-%Y_%Hh%Mm%Ss")
    for set in data_sets:
        set = str(set)
        if len(set) < 2:
            set = '0' + set
        write_results(transfer_data(tc, args.src_ep_id, args.dest_ep_id, '/datasets/ds{}'.format(set),
                      '/scratch/mmoo97/TEST_TRANSFER/ds{}'.format(set), True), "{}.csv".format(test_start))

    for set in data_sets:
        set = str(set)
        if len(set) < 2:
            set = '0' + set
        write_results(transfer_data(tc, args.dest_ep_id, args.src_ep_id,
                                    '/scratch/mmoo97/TEST_TRANSFER/ds{}'.format(set), '/perftest/uab_rc/ds{}'.format(set),
                                    True), "{}.csv".format(test_start))
