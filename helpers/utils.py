import base64
import json
from types import SimpleNamespace


def json_to_object(jsonStr: str):
    ''' Convert JSON string into object so that its elements can be easily accessed
    '''
    return json.loads(jsonStr, object_hook=lambda d: SimpleNamespace(**d))


def json_to_dict(jsonStr: str):
    ''' Convert JSON string into dict so that its elements can be easily accessed
    '''
    return json.loads(jsonStr)


def base64_decode(str:str):
    ''' Decode a given string using Base 64 and output as UTF-8 string
    '''
    return base64.b64decode(str).decode('utf-8')


def base64_encode(str:str):
    ''' Encode a given string using Base64 by converting the string into bytes using UTF-8. Output as ASCII string.
    '''
    return base64.b64encode(bytes(str, 'utf-8')).decode('ascii')
