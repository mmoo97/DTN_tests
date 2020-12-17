import globus_sdk
import argparse
from time import sleep
import progressbar
import csv
from datetime import datetime


def get_args():
    """
    Command line parsing function that leverages the argparse library. Call use cases via "python generate_data.py -h"
    or "python generate_data.py --help".

    @return: An argparse object that contains all of the aruguments provided based on the paramenters below.

    """
    parser = argparse.ArgumentParser(description='Capture Globus transfer speeds between two endpoints.')
    parser.add_argument('client', type=str, help='The Client ID of the account testing the transfers')
    parser.add_argument('src_ep_id', type=str, help='The Endpoint ID of the source endpoint.')
    parser.add_argument('dest_ep_id', type=str, help='The Endpoint ID of the destination endpoint.')
    parser.add_argument('src_dir', type=str, help='The desired directory from the source endpoint.')
    parser.add_argument('dest_dir', type=str, help='The desired directory from the destination endpoint.')
    parser.add_argument('-t, --refresh-token', dest='refresh_token', type=str,
                        help='The resource token for Globus Authentication.')
    parser.add_argument('-r', dest='return_directory', type=str,
                        help='The directory to write to if destination write is specified')
    parser.add_argument('-w', dest='write_back', action='store_true',
                        help='Write data written to the destination directory back to the source directory or the '
                             'specified return directory using [-r].')
    parser.add_argument('-c', dest='clean', action='store_true',
                        help='Use to delete/clean the transferred files post transfer.')
    parser.add_argument('-b', dest='batch', action='store_true',
                        help='Run all transfers at the same time rather than individually.')

    return parser.parse_args()


def get_authorizer(client_id, **kwargs):
    """
    Function that takes in a Globus App Client ID and returns either a Globus AccessTokenAuthorizer or
    RefreshTokenAuthorizer Object.

    @param client_id: (string) Globus App Client ID.
    @param kwargs: refresh_token=(string) Refresh token delivered by the command line/the Globus Api.
    @return:
    """
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
        print("\tRefresh token:\t" + globus_transfer_data['refresh_token'] + "\n")  #Refresh Token for later use

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


def single_transfer_data(tc, src_id, dest_id, src_dir, dest_dir, output):
    """
    Will initiate the transfer of a single dataset and show the progress in the console.

    @param tc: (globus_sdk.transfer.client.TransferClient) Client to conduct the transfer.
    @param src_id: (string) Globus endpoint id of the Source endpoint.
    @param dest_id: (string) Globus endpoint id of the Destination endpoint.
    @param src_dir: (string) Source directory where the datasets are contained and originating from.
    @param dest_dir: (string) Destination directory where the datasets are contained and being returned to.
    @param output: (boolean) Whether or not to show output of transfers. (CURRENTLY DEFAULTED TO TRUE)

    @return: (dictionary) Object that contains transfer details and results.
    """
    tdata = globus_sdk.TransferData(tc, src_id,
                                    dest_id,
                                    label="Add {}".format(src_dir.split("/")[-1]),
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
                print("Effective Speed: " + str(round(task["effective_bytes_per_second"] / (1024 * 1024), 2)) + " MB/s")

            return {"dataset": src_dir.split("/")[-1],
                    "start": task["request_time"],
                    "end": task["completion_time"],
                    "elapsed": str(bar.data()['time_elapsed']),
                    "speed": str(round(task["effective_bytes_per_second"] / (1024 * 1024), 2)),
                    "src_ep_id": src_id,
                    "dest_ep_id": dest_id,
                    "task_id": transfer_result["task_id"]}

        elif task["status"] == "ACTIVE":
            if output:
                bar.update(round(task["bytes_transferred"] / 1000000, 2))
                sleep(.5)

        else:
            if output:
                bar.finish()
                print("\rTask Status: %s\n" % task["status"])
            exit(-1)


def multi_transfer(tc, src_id, dest_id, src_dir, dest_dir, output):
    """
    Will initiate the transfer of a multiple datasets (ds01-ds16) and show the progress in the console. Will submit all
    transfers as a batch given the "-b" flag in the console.
    @param tc: (globus_sdk.transfer.client.TransferClient) Client to conduct the transfer.
    @param src_id: (string) Globus endpoint id of the Source endpoint.
    @param dest_id: (string) Globus endpoint id of the Destination endpoint.
    @param src_dir: (string) Source directory where the datasets are contained and originating from.
    @param dest_dir: (string) Destination directory where the datasets are contained and being returned to.
    @param output: (boolean) Whether or not to show output of transfers. (CURRENTLY DEFAULTED TO TRUE)

    @return: (dictionary) Object that contains transfer details and results.
    """
    data_sets = ["01", "04", "06", "08", "10", "12", "14", "16"]

    if args.batch:
        ready_transfers = []
        submitted_data = []
        for set in data_sets:
            data = globus_sdk.TransferData(tc, src_id, dest_id, label="Add ds{} Batch".format(set),
                                           sync_level=None, verify="checksum")
            data.add_item(src_dir + "ds{}".format(set), dest_dir + "ds{}".format(set), recursive=True)
            ready_transfers.append(data)
            transfer_result = tc.submit_transfer(data)
            submitted_data.append(transfer_result)

    else:

        for set in data_sets:
            write_results(single_transfer_data(tc, args.src_ep_id, args.dest_ep_id, src_dir + 'ds{}'.format(set),
                                               dest_dir + 'ds{}'.format(set), output),
                          "{}.csv".format(test_start))

        if args.write_back:
            ddir = args.return_directory or args.src_dir
            for set in data_sets:
                write_results(single_transfer_data(tc, args.dest_ep_id, args.src_ep_id,
                                                   dest_dir + 'ds{}'.format(set),
                                                   ddir + 'ds{}'.format(set),
                                                   output), "{}.csv".format(test_start))


def write_results(data_dict, filename):
    """
    Takes a single output dictionary and writes the results to a .csv file.
    @param data_dict: (dictionary) Data to write to the .csv file.
    @param filename: (string) Filename of the .csv file to write to.
    @return: Outputs .csv file.
    """
    with open(filename, 'a+', newline='') as file:
        writer = csv.writer(file)

        if file.tell() == 0:
            writer.writerow(["Dataset", "Start", "End", "Elapsed", "Speed", "Source EP ID", "Dest. EP ID", "Task ID"])

        if args.batch:
            pass
        else:
            writer.writerow([data_dict["dataset"],
                             data_dict["start"],
                             data_dict["end"],
                             data_dict["elapsed"],
                             data_dict["speed"],
                             data_dict["src_ep_id"],
                             data_dict["dest_ep_id"],
                             data_dict["task_id"]])


def clean():
    """
    Deletes the written data from the endpoints.
    @return: None
    """
    if args.clean:
        ddata = globus_sdk.DeleteData(tc, args.dest_ep_id, recursive=True,
                                      label="Delete {}".format(args.dest_dir.split("/")[-1]))

        ddata.add_item(args.dest_dir)
        tc.submit_delete(ddata)

        if args.write_back and (args.return_directory is not None):  # Ensure that data is not deleted from host.
            ddir = args.return_directory or args.src_dir
            ddata2 = globus_sdk.DeleteData(tc, args.src_ep_id, recursive=True,
                                           label="Delete {}".format(args.src_dir.split("/")[-1]))
            ddata2.add_item(ddir)
            tc.submit_delete(ddata2)


if __name__ == '__main__':
    args = get_args()
    authorizer = get_authorizer(args.client,
                                refresh_token=args.refresh_token)
    tc = globus_sdk.TransferClient(authorizer=authorizer)

    test_start = datetime.now().strftime("%m-%d-%Y_%Hh%Mm%Ss")

    multi_transfer(tc, args.src_ep_id, args.dest_ep_id, args.src_dir, args.dest_dir, True)
    clean()
