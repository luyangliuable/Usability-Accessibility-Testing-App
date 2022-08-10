from flask import jsonify, send_file
from celery import Celery, current_task
from celery.result import AsyncResult
# from scan_app.app import *
import time
import os
import requests

celery = Celery(__name__)
celery.conf.broker_url = os.environ['REDIS_URL']
celery.conf.result_backend = os.environ['REDIS_URL']



@celery.task(name="run_storydistiller")
def run_storydistiller(info={}):
    ###############################################################################
    #                                Storydistiller                               #
    ###############################################################################
    errors = []
    uuid = info["uuid"]

    # Story distiller api url to be obtained from the enrionemtn ###############
    story_distiller_api = os.environ.get("STORYDISTILLER")
    story_distiller_api = "http://host.docker.internal:3002/new_job"

    try:
        algorithm = "storydistiller"
        print("[1] Running Storydistiller")
        result = requests.post(story_distiller_api, json={ "uid": uuid })
        # time.sleep(3);
    except Exception as ex:
        print('failed to complete tasks', algorithm, "with url", story_distiller_api, "because", ex)
        errors.append(ex)
    else:
        print("Successfully connected completed tasks", algorithm)
        state = {"task_id": "", "task_status": ['distiller'], "task_result": ""}

    result = {"files": ["file_url_placeholder"], "images": ["image_url_placeholder"], "errors": str( errors ) }

@celery.task(name="create_task")
def create_task(info):
    ###############################################################################
    #                           Create celery web tasks                           #
    ###############################################################################

    print("Now inside celery....")

    # TODO signal all algorithms to start.

    # xbot api url to be obtained from the enrionemtn ##########################
    xbot_api = os.environ.get("XBOT")
    # xbot_api = "http://host.docker.internal:3003/new_job"

    # xbot api url to be obtained from the enrionemtn ##########################
    owleye_api = os.environ.get("OWLEYE")
    # owleye_api = "http://host.docker.internal:3004/new_job"

    ###############################################################################
    #                               Obtain task uuid                              #
    ###############################################################################
    print(info)
    uuid = info['uuid']

    ###############################################################################
    #                            Obtain celery task id                            #
    ###############################################################################
    task_id = celery.current_task.request.id

    celery.AsyncResult("task_id").status = "asdasdads";
    print(celery.AsyncResult("task_id").state)

    ###############################################################################
    #                          Store errors and warnings                          #
    ###############################################################################
    errors = []

    #######################################################################################################
    # NOTE: In order for the next part to work both flask_backend and worker but be running inside docker #
    #######################################################################################################

    print("Celery task received uuid is", uuid)

    ###############################################################################
    #                                PIPELINE START                               #
    ###############################################################################

    ###############################################################################
    #                                Storydistiller                               #
    ###############################################################################
    try:
        algorithm = "storydistiller"
        print("[1] Running Storydistiller")
        # result = requests.post(story_distiller_api, json={ "uid": uuid })
        time.sleep(3);
    except Exception as ex:
        print('failed to complete tasks', algorithm, "with url", story_distiller_api, "because", ex)
        errors.append(ex)
    else:
        print("Successfully connected completed tasks", algorithm)
        state = {"task_id": "", "task_status": ['distiller'], "task_result": ""}
        current_task.update_state(state="sadasd")


    ###############################################################################
    #                                    Xbot                                     #
    ###############################################################################
    try:
        algorithm = "xbot"
        result = requests.post(xbot_api, json={ "uid": uuid })

        print(result.status_code)
        print(result.text)
        print(result.content)
    except Exception as ex:
        print('failed to complete tasks', algorithm, "with url", xbot_api, "because", ex)
        errors.append(ex)
    else:
        print("Successfully connected completed tasks", algorithm)
        current_task.update_state('PROGRESS', meta={"task_id": "", "task_status": ['xbot'], "task_result": "sadasd"})


    ###############################################################################
    #                                   owleye                                    #
    ###############################################################################
    print("task completed")

    result = {"files": ["file_url_placeholder"], "images": ["image_url_placeholder"], "errors": str( errors ) }

    return result, 200
