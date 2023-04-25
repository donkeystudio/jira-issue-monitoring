from server.apikey_resource import APIKeyResource
import helpers.utils as utils
from flask import request

class RequestReport(APIKeyResource):

    callback_func: None

    def __init__(self, *args) -> None:
        self._config = args[0][0]
        self.callback_func = args[0][1]


    def get_config_apikey(self):
        if self._config.api_key.key:
            return utils.base64_decode(self._config.api_key.key)
        else:
            return ""
    

    def get_request_schema(self):
        return utils.json_namespace_to_dict(self._config.request_schema)
    

    def get_header_apikey(self):
        api_key = ""
        if self._config.api_key.header and self._config.api_key.header in request.headers:
                api_key = request.headers[self._config.api_key.header]

        return api_key
    

    def process_post(self):

        if request.is_json:
            pay_load = self.process_payload()
            
            project_key = None
            if hasattr(pay_load, "project"):
                project_key = pay_load.project
                self._logger.info(f'Receiving request to generate report for project: {project_key}.')
            else:
                self._logger.info(f'Receiving request to generate report for all projects.')

            message = self.callback_func(project_key)

            if message:
                return {'status':200, 'report': message}, 200
            else:
                return {'status': 200, 'message': f'There is no report available for project {project_key}'}
        else:
            return {'status': 415, 'message': 'Come on! Give me JSON payload!'}, 415