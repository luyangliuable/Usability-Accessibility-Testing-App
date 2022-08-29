from botocore import endpoint
from botocore.compat import accepts_kwargs
import pymongo
import boto3
import json
import requests
import os
from os import path
import subprocess
import tempfile
from flask import Flask, request, jsonify

from converter.run import convert_droidbot_to_gifdroid_utg

app = Flask(__name__)

###############################################################################
#        Load user config file gifdroid algorithm running configuration       #
###############################################################################

with open("config.json", "r") as f:
    config = json.load(f)

endpoint_url = os.environ.get("S3_URL")

if endpoint_url == None:
    endpoint_url = config['ENDPOINT_URL']

status_api = str( os.environ.get("STATUS_API") )

file_api = str( os.environ.get("FILE_API") )

if file_api == None:
    endpoint_url = config['FILE_API']


EMULATOR = os.environ.get( "EMULATOR" )

if EMULATOR == None:
    EMULATOR = config['EMULATOR']


###############################################################################
#                                Set up AWS S3                                #
###############################################################################


boto3.setup_default_session(profile_name=config[ 'AWS_PROFILE' ])
s3_client = boto3.client(
    "s3",
    region_name=config['AWS_REGION'],
    endpoint_url=endpoint_url,
)


###############################################################################
#                              Connect to mongodb                             #
###############################################################################
try:
    connection = pymongo.MongoClient(os.environ.get("MONGO_URL"))
    _db = connection.fit3170
    connection.server_info()  # Triger exception if connection fails to the database
except Exception as ex:
    print('failed to connect', ex)
else:
    print("Successfully connected to mongodb.")


@app.route("/new_job", methods=["POST"])
def send_uid_and_signal_run():
    """
    This function creates a new job for gifdroid and droidbot to run together.

    POST req input:
    uid - The unique ID for tracking all the current task.
    """
    if request.method == "POST":
        print('NEW JOB FOR UUID: ' + request.get_json()["uid"])

        # Get the UUID from the request in json #######################################
        uid = request.get_json()["uid"]

        # Execute droidbot ############################################################
        _service_execute_droidbot(uid)

        # Execute gifdroid ############################################################
        _service_execute_gifdroid(uid)

        return jsonify( {"result": "SUCCESS"} ), 200

    return "No HTTP POST method received"

def _service_execute_droidbot(uuid):
    """
    This function execute droidbot algorithm responsible for getting the utg.js file.

    Parameters:
        uuid - The unique id for the current task.
    """

    print('Beginning new job for %s' % uuid)

    data={
        'algorithm': 'gifdroid',
        'status': 'RUNNING', # TODO create enum
        'notes': 'executing droidbot to generate utg file',
        'estimate_remaining_time': 60*3
    }

    update_app_status(uuid, data)

    ###############################################################################
    #                      GET the APK file name from mongodb                     #
    ###############################################################################
    print("[1] Getting session information")

    data = requests.get(file_api, headers={'Content-Type': 'application/json'},  data=json.dumps( {'uuid': uuid} )).json()

    # Apk has an Array/List of apk files ##########################################
    apk_filename = data['apk'][0]['name']

    ############################################################################
    #                    Download file into temporary folder                   #
    ############################################################################
    temp_dir = tempfile.gettempdir()

    print("[2] Getting file from bucket using UUID " + uuid + " and apk file " + apk_filename + ".")

    target_apk = path.join(temp_dir, apk_filename)

    s3_client.download_file(
        Bucket='apk-bucket',
        Key=path.join(uuid, apk_filename),
        Filename = target_apk
    )

    ############################################################################
    #                      Run program with downloaded apk                     #
    ############################################################################
    OUTPUT_DIR = "./"

    print("[3] Running Droidbot app")

    subprocess.run([ "adb", "connect", EMULATOR])

    os.chdir("/home/droidbot")
    subprocess.run([ "droidbot", "-count", config[ "NUM_OF_EVENT" ], "-a", target_apk, "-o", OUTPUT_DIR])

    ###############################################################################
    #                                Save utg file                                #
    ###############################################################################
    print("[4] Saving utg.js file to bucket.")

    enforce_bucket_existance([config[ "BUCKET_NAME" ], "storydistiller-bucket", "xbot-bucket"])

    #Upload events folder
    upload_directory("events", config["BUCKET_NAME"])

    #Upload states folder
    upload_directory("states", config["BUCKET_NAME"])

    # Upload utg
    s3_client.upload_file(config[ "DEFAULT_UTG_FILENAME" ], config[ 'BUCKET_NAME' ], os.path.join(uuid, config[ "DEFAULT_UTG_FILENAME" ]))

    ###############################################################################
    #                                Update mongodb                               #
    ###############################################################################

    print("[5] Updating database for traceability of utg file")
    print("Saving into entry", uuid)

    _db.apk.update_one(
        {
            "uuid": uuid
        },
        {
            "$set": {
                "utg_files": config["DEFAULT_UTG_FILENAME"]
            }
        }
    )


def _service_execute_gifdroid(uuid):
    # retrieve utg file name from mongodb

    data={
        'algorithm': 'gifdroid',
        'status': 'RUNNING', # TODO create enum
        'notes': 'executing gifdroid to generate execution trace file',
        'estimate_remaining_time': 60
    }

    update_app_status(uuid, data)

    ###############################################################################
    #                        Get utg filename from mongodb                        #
    ###############################################################################
    print("[1] Getting utg filename from mongodb")

    print("[2] Creating temporary file to save utg file")

    ###############################################################################
    #                        Convert utg to correct format                        #
    ###############################################################################
    convert_droidbot_to_gifdroid_utg(os.path.join("/home/droidbot", config['DEFAULT_UTG_FILENAME']),"/home/droidbot/events", "/home/droidbot/states")

    ###############################################################################
    #                          Get gif file from frontend                         #
    ###############################################################################
    os.chdir("/home/gifdroid")

    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

    response = requests.get("http://host.docker.internal:5005/file/get", data=json.dumps( {"uuid": uuid} ), headers=headers)

    lookup = response.json()

    for item in lookup['additional_files']:
        if item['algorithm'] == 'gifdroid':
            gif_file = item['name']

    s3_client.download_file(
        Bucket=config["BUCKET_NAME"],
        Key=path.join(uuid, gif_file),
        Filename = gif_file
    )

    ###############################################################################
    #                               Run GIFDROID app                              #
    ###############################################################################
    print("[3] Running GIFDROID app")


    subprocess.run([ "python3", "main.py", "--video=./" + gif_file, "--utg=" + "../droidbot/utg.json", "--artifact=../droidbot/output", "--out=" + config["OUTPUT_FILE"]])

    #save output file to bucket
    enforce_bucket_existance([config[ "BUCKET_NAME" ], "storydistiller-bucket", "xbot-bucket"])


    print("[4] Uploading gif file to bucket")
    s3_client.upload_file(config[ "OUTPUT_FILE" ], config[ 'BUCKET_NAME' ], os.path.join(uuid, config[ "OUTPUT_FILE" ] ))

    #update mongodb
    print("[5] Updating mongodb for traceability")
    _db.apk.update_one(
        {
            "uuid": uuid
        },
        {
            "$set": {
                "gifdroid_files": [config["OUTPUT_FILE"]]
            }
        }
    )

    download_link = os.path.join( "http://localhost:5005", "download_result", uuid) + "/gifdroid_files"

    update_app_attribute(uuid, 'status', "DONE")
    update_app_attribute(uuid, 'download_link', download_link)

    return 200


@app.route("/", methods=["GET"])
def check_health():
    """
    Check that gifdroid is in good health.
    """

    return "Gifdroid is live!"

###############################################################################
#                              Utility Functions                              #
###############################################################################

def bytes_to_json(byte_str: bytes):
    data = byte_str.decode('utf8').replace("'", '"')
    data = json.loads(data)

    return data

def upload_directory(path, bucketname):
    for root,dirs,files in os.walk(path):
        for file in files:
            s3_client.upload_file(os.path.join(root,file),bucketname,file)


def enforce_bucket_existance(buckets):
    for bucket in buckets:
        try:
            s3_client.create_bucket(Bucket=bucket, CreateBucketConfiguration={'LocationConstraint': 'us-west-2'})
        except:
            print("Bucket already exists %s".format( bucket ))


def update_app_attribute(uuid, attribute, val):
    # NOTE the request link MUST NOT have an additional /
    request_url = os.path.join( status_api, 'update', uuid, 'gifdroid') + "/" + attribute
    res = requests.post(request_url, headers={'Content-Type': 'application/json'}, data=str( val ))
    print(request_url)
    print(res.content)

    return res


def update_app_status(uuid, status):
    # NOTE the request link MUST NOT have an additional /
    request_url = os.path.join( status_api, 'update') + "/" + uuid
    res = requests.post(request_url, headers={'Content-Type': 'application/json'}, data=json.dumps( status ))
    print(request_url)
    print(res.content)

    return res


if __name__ == "__main__":
    # No point doing debug mode True because can't debug on docker
    app.run(host="0.0.0.0", port=3005)
    # data={
    #     "estimate_remaining_time": 60
    # }

    # update_app_status("57730388-de61-45c1-8098-d449491004ec", data)
    # update_app_attribute("608883a9-4241-4f2b-8053-0ece386cd7ae", 'result_link', 'poofoobar')
    # update_app_attribute("608883a9-4241-4f2b-8053-0ece386cd7ae", 'status', 'DONE')



