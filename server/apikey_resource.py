from configparser import ConfigParser
import logging
from flask import request
from flask_restful import Resource
import helpers.utils as utils
from jsonschema import validate, FormatChecker

class APIKeyResource(Resource):
    ''' Resource class with API KEY Authentication supported
    '''
    
    CONFIG_SECTION=""
    CONFIG_KEY="CONFIG"

    __name__ = 'APIKEYResource'
    _config = None
    _logger = logging.getLogger(__name__)

    def __init__(self, *args) -> None:
        super().__init__()
        config_parser = ConfigParser()
        config_parser.read(args[0][0])

        try:
            if config_parser.has_option(self.CONFIG_SECTION, self.CONFIG_KEY):
                self._config = utils.json_to_object(config_parser.get(self.CONFIG_SECTION, self.CONFIG_KEY))
            else:
                self._logger.fatal(f"CONFIG is NOT found under {self.CONFIG_SECTION} section")
        except:
            self._logger.fatal("Configuration setup failed!")

    def get(self):
        return self.process_get()
    
    def post(self):
        api_key = self.get_header_apikey()

        if api_key is not None and api_key == self.get_config_apikey():
            try:
                pay_load = self.process_payload()
                json_pay_load = utils.json_namespace_to_dict(pay_load)
                json_schema = self.get_request_schema()
                validate(instance=json_pay_load, schema=json_schema, format_checker=FormatChecker())
                return self.process_post()
            except Exception as error:
                self._logger.error (f'Receive invalid request with error: {error}')
                return self.process_invalid_schema()

        return self.process_invalid_apikey()


    def process_post(self):
        return {'status': 501, 'message': 'Method not supported'}, 501


    def process_get(self):
        return {'status': 501, 'message': 'Method not supported'}, 501


    def process_put(self):
        return {'status': 501, 'message': 'Method not supported'}, 501


    def process_payload(self):
        return utils.json_to_object(request.get_data(as_text=True))
    

    def process_invalid_schema(self):
        return {'status': 400, 'message': 'Invalid request data'}, 400
    

    def process_invalid_apikey(self):
        return {'status': 401, 'message': 'Authorization failed'}, 401
    

    def get_config_apikey(self):
        return ""
    

    def get_request_schema(self):
        return {}
    

    def get_header_apikey(self):
        return None