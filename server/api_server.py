from flask import Flask
from flask_restful import Api


class APIServer:
    ''' Main class to setup API Server. For each API end-point, call add_resource function.
        Use AuthResource if the end-point supports Basic HTTP Authentication
        Use HMACResource if the end-point supports HMAC secret key authentication
    '''
    app: Flask
    api: Api

    def __init__(self, app_name) -> None:
        self.app = Flask(app_name)
        self.api = Api(self.app)

    def add_resource(self,resource, route: str, *args):
        self.api.add_resource(resource.__class__, route, resource_class_args=[*args])


    def start(self, host: str, port: int, **kwargs):
        self.app.run(debug = kwargs.get('debug', False), host = host, port = port, use_reloader = False)