import os
# from numpy import result_type
from utility.uuid_generator import unique_id_generator
from typing import TypeVar, Generic, List, Dict, Tuple
from controllers.controller import Controller
from enums.status_enum import StatusEnum
from models.DBManager import DBManager


T = TypeVar('T')


class AlgorithmDataController(Generic[T], Controller):
    """
    This controller class is used to update metadata for files on mongodb for traceability purpose.
    """

    results_key = "results"

    def __init__(self, collection_name: str) -> None:
        """
        This controller class is used to update metadata for files on mongodb for traceability purpose.

        Parameters:
            collection_name - (str) name of collection on *mongodb* which is apk.
            json_result_file_parser - (Strategy) will not be used but still not updated because backend not finished

        Returns: None
        """
        self.collection_name = collection_name
        self._db = DBManager.instance()
        self.collection = self._db.get_collection('apk')

        self.lookup = {
            "owleye": "activities",
            "storydisitiller": "activities",
            "xbot": "activities",
            "gifdroid": "gifdroid",
            "droidbot": "gifdroid",
        }

    def get(self, uuid: str):
        """
        Get file metadata that matches the job uuid

        Parameters:
            uuid (str) - The job uuid the identifies the cluster of algorithms to run
        """

        return self._db.get_document(uuid=uuid, collection=self.collection)


    def post(self, uuid: str, algorithm: str, new_data: T) -> bool:
        """
        Add file metadata that matches the job uuid


        Parameters:
            request_parameters - request parameters that contain contents of document
        """

        self.collection.update_one({"uuid": uuid}, {'$push': {f'results.ui-states.{ algorithm }': new_data}})

        result = self._db.get_document(uuid, self.collection)[self.results_key]['ui-states'][algorithm]

        return result


    def _insert_utg_result(self, uuid: str, data: Dict) -> Dict[str, T]:
        results_schema = self._db.get_format(uuid)[self.results_key]

        results_schema['utg'] = data;

        self._db.update_document(uuid, self.collection, self.results_key, results_schema)

        return results_schema;


    def _insert_algorithm_result(self, uuid: str, data: Dict[str, List]) -> Dict[str, T]:
        """
        This function inserts the links to the algorithm results into the document matching uuid

        Parameters:
            uuid - uuid for the job which is the cluster of algorithms tasked to run
            algorithm - the algorithm the result links for
            links_to_res - the single link to result. NOTE that element in list is dynamically typed so it can be a string

        Returns: Dictionary for the updated document and a bool if the method is successful.

        """

        # document = self._db.get_document(uuid, self.collection)
        results_key = "results"
        result_schema = self._db.get_format(uuid)[results_key]
        alg_results = dict(result_schema)


        new_gifdroid = alg_results['gifdroid']

        for key, item in data.items():
            if key == "ui-states":
                new_activities = []
                for each_activity in item:
                    print(each_activity)
                    new_activity = self._db.get_format(uuid)[results_key]['activities'][0]
                    for name, data in each_activity.items():
                        if name == 'activity-name':
                            new_activity[name] = each_activity[name]
                        elif name == 'structure-id':
                            new_activity[name] = each_activity[name]
                        elif name == 'base-image':
                            new_activity[name] = each_activity[name]
                        elif name == "xbot":
                            new_activity[name]['image'] = each_activity[name]['image']
                            new_activity[name]['description'] = each_activity[name]['description']
                        elif name == "owleye":
                            new_activity[name]['image'] = each_activity[name]['image']
                        elif name == "tappable":
                            # assert 'tappable' in new, "New must have tappable"
                            # assert 'tappable' in each_activity, "Each activity must have tappable"
                            new_activity[name]['image'] = each_activity[name]['image']
                            new_activity[name]['description'] = each_activity[name]['description']
                            new_activity[name]['heatmaps'] = each_activity[name]['heatmaps']
                    new_activities.append(new_activity)

                if len(new_activities) > 0:
                    alg_results['activities'] = new_activities

            elif key == 'gifdroid':
                for name, data in item.items():
                    new_gifdroid[name] = data

        self._db.update_document(uuid, self.collection, results_key, alg_results)

        return alg_results


    def _get_utg(self, uuid: str) -> Dict[str, T]:
        """
        Method for getting a document from api

        Parameters:
            uuid - the unique id for the job containing algorithm run.
            algorithm - the algorithm

        Returns: The result slice in the schema for the algorithm

        """

        document = self.get(uuid)
        result = document[self.results_key]['utg']

        return result


    def _get_result_of_algorithm(self, uuid: str, type: str) -> Dict[str, T]:
        """
        Method for getting a document from api

        Parameters:
            uuid - the unique id for the job containing algorithm run.
            algorithm - the algorithm

        Returns: The result slice in the schema for the algorithm

        TODO: fix this method to return the correct result
              Currently it returns the entire document and not just the results for the algorithm
        """

        schema_result_key = 'results'
        document = self.get(uuid)
        result = document[schema_result_key][type]

        return result

    def _get_lookup(self) -> Dict[str, str]:
        return self.lookup
