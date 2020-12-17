# Introduction
This is a [Globus-API](https://docs.globus.org/api/) application that will run DTN transfer tests and output a .csv data
and additionally talk that data and display it in a jupyter notebook. This project was inspired by 
[ESnet's Data Mobility Exhibition](https://fasterdata.es.net/performance-testing/2019-2020-data-mobility-workshop-and-exhibition/2019-2020-data-mobility-exhibition/)
and has guidelines and requisites posted [here](https://www.globusworld.org/tour/data-mobility-exhibition). READ ALL OF 
THE [GUIDELINES](https://www.globusworld.org/tour/data-mobility-exhibition) BEFORE USING THIS TOOL.
# Project Setup 


To clone this repo use the command: 
```
$ git clone [placeholder]
$ cd DTN_tests
```
## Prerequisites
### Get a DME Endpoint Access Membership
In order to access the datasets that will be used, you must [request a membership](https://app.globus.org/groups/3ca64c67-9daf-11e9-855f-0e45b29ab6fa/join)
which gives you access to a small range of endpoints.
### Setup a Virtual Environment
- Ensure you have created a [virtual environment](https://docs.python.org/3/library/venv.html) 
called `venv` setup running python3.
  - Note, this project requires a virtual environment running __python3__.
    - Create this by navigating to you home directory via typing `$ cd` and entering the following commands:<br>
    ```
    $ python3 -m venv ~/venv
    $ source ~/venv
    ``` 
    - Upon Activation, you should see the prompt update accordingly:
    ```
    [centos@ood ~]$              <------Old Prompt
    (venv) [centos@ood ~]$       <------New Prompt
    ```
    In this case, the env name is displayed as `venv` but would change to reflect whatever name you initialized it with
    in the previous step. Additionally, this example is running on the `ood node` provisioned
    via __OpenStack__.
- Ensure [pip](https://docs.python.org/3/installing/index.html) is installed.
  - #### Mac/Linux
    - Check if installed by typing `$ pip`
    - Install pip using `$ python -m pip install --user --upgrade pip`.
  - #### Windows
    - Check if installed using `$ py`
    - Install pip using `$ py -m pip install --upgrade pip`<br><br>
- Ensure all dependencies are installed to you virtual environment  using the following commands:
```
$ cd ~/your/repo/path/DTN_tests
$ pip install -r requirements.txt
```
### Get a Globus Client
Follow [Step 1:](https://globus-sdk-python.readthedocs.io/en/stable/tutorial.html#tutorial-step1) and 
[Step 2:](https://globus-sdk-python.readthedocs.io/en/stable/tutorial.html#step-2-get-and-save-client-id) in the Globus
SDK tutorial to get a client ID to be used to carry out your transfers later in the project. 
## Capture Data
In order to transfer data, you will need your client id to be supplied to the `generate_data.py` script which is run
according to the usage message below:
```
usage: generate_data.py [-h] [-t, --refresh-token REFRESH_TOKEN] [-r RETURN_DIRECTORY] [-w] [-c] [-b] client src_ep_id dest_ep_id src_dir dest_dir

Capture Globus transfer speeds between two endpoints.

positional arguments:
  client                The Client ID of the account testing the transfers
  src_ep_id             The Endpoint ID of the source endpoint.
  dest_ep_id            The Endpoint ID of the destination endpoint.
  src_dir               The desired directory from the source endpoint.
  dest_dir              The desired directory from the destination endpoint.

optional arguments:
  -h, --help            show this help message and exit
  -t, --refresh-token REFRESH_TOKEN
                        The resource token for Globus Authentication.
  -r RETURN_DIRECTORY   The directory to write to if destination write is specified
  -w                    Write data written to the destination directory back to the source directory or the specified return directory using [-r].
  -c                    Use to delete/clean the transferred files post transfer.
  -b                    Run all transfers at the same time rather than individually.
```
This script will generate an output file to the current directory in the format `[START_TIMESTAMP].csv`. This version
will take a single pair of endpoints and run either 8 or 16 (to and from the source if specified) transfers. 

An example execution of the script would look something like the following
```
python generate_data.py [your client id] [source_endpoint_id] [cheaha_endpoint_id] /datasets/ /data/user/mmoo97/TEST_TRANSFER/ -t $TOKEN -b -wr /perftest/uab_rc/
```
