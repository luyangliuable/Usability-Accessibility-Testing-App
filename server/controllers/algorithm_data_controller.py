from utility.uuid_generator import unique_id_generator
from typing import TypeVar, Generic, List, Dict, Tuple
from download_parsers.strategy import Strategy
from controllers.controller import Controller
from enums.status_enum import StatusEnum
from models.DBManager import DBManager


T = TypeVar('T')


class AlgorithmDataController(Generic[T], Controller):
    """
    This controller class is used to update metadata for files on mongodb for traceability purpose.
    """

    def __init__(self, collection_name: str, json_result_file_parser: Strategy) -> None:
        ###############################################################################
        #                          Initiate database instance                         #
        ###############################################################################
        self.cn = collection_name
        self._db = DBManager.instance()

        ###############################################################################
        #                               Update stratefy                               #
        ###############################################################################
        self._strategy = json_result_file_parser

        self.c = self._db.get_collection('apk')

        self.lookup = {
            "owleye": "activity",
            "storydisitiller": "activity",
            "xbot": "activity",
            "gifdroid": "gifdroid",
            "droidbot": "gifdroid",
        }


    def insert_algorithm_result(self, uuid: str, algorithm: str, links_to_res: List, result_type: str, file_names: List) -> Tuple[ Dict[str, T], int]:
        """
        This function inserts the links to the algorithm results into the document matching uuid

        Parameters:
            uuid - uuid for the job which is the cluster of algorithms tasked to run
            algorithm - the algorithm the result links for
            links_to_res - the single link to result. NOTE that element in list is dynamically typed so it can be a string

        Returns: Dictionary for the updated document and a bool if the method is successful.

        """
        ###############################################################################
        #                             Convert file to json                            #
        ###############################################################################
        result_key_in_d = "results"

        # Get document matching uuid ############################################
        d = self._db.get_document(uuid, self.c)

        # Get the results segment #####################################################
        result = d[result_key_in_d]

        # Change document and insert result link ######################################
        prev = result[self.lookup[algorithm]][result_type]
        parsed_json_for_schema = self._strategy.do_algorithm(uuid, links_to_res, file_names)

        # Append new parsed json to schema ############################################
        result[self.lookup[algorithm]][result_type] = prev + parsed_json_for_schema

        # Update result back #####################################################
        self._db.update_document(uuid, self.c, result_key_in_d, result)

        return result, 200


    def get(self, uuid: str):
        """
        Get file metadata that matches the job uuid

        Parameters:
            uuid (str) - The job uuid the identifies the cluster of algorithms to run
        """

        return self._db.get_document(uuid=uuid, collection=self.c)


    def post(self, request_parameters: List, document: Dict) -> bool:
        """
        Add file metadata that matches the job uuid


        Parameters:
            request_parameters - request parameters that contain contents of document
        """

        try:
            ###############################################################################
            #                         Add file metadata to mongodb                        #
            ###############################################################################

            for each_key, _ in document.items():
                document[each_key] = request_parameters[each_key]

            document['uuid'] = unique_id_generator()

            self._db.insert_document(document, self.c).inserted_id

            return True
        except Exception as e:
            ###############################################################################
            #                                Error Handling                               #
            ###############################################################################
            raise IndexError(str(e))


    def get_result_of_algorithm(self, uuid: str, algorithm: str) -> Dict[str, T]:
        """
        Method for getting a document from api

        Parameters:
            uuid - the unique id for the job containing algorithm run.
            algorithm - the algorithm

        Returns: The result slice in the schema for the algorithm
        """

        schema_result_key = 'results';
        document = self.get(uuid)
        print(document)
        result = document[schema_result_key][algorithm]

        return result


    def get_lookup(self) -> Dict[str, str]:
        return self.lookup