import base64
import json
import re
from types import SimpleNamespace


def json_to_object(jsonStr: str):
    ''' Convert JSON string into object so that its elements can be easily accessed
    '''
    return json.loads(jsonStr, object_hook=lambda d: SimpleNamespace(**d))

def json_namespace_to_dict(jsonObject):
    ''' Convert SimpleNameSpace JSON into dict so that its elements can be easily accessed
    '''
    return json.loads(json_ns_to_str(jsonObject))

def json_to_dict(jsonStr: str):
    ''' Convert JSON string into dict so that its elements can be easily accessed
    '''
    return json.loads(jsonStr)

def json_ns_to_str(jsonObject):
    ''' Convert SimpleNameSpace JSON into String
    '''
    return json.dumps(jsonObject, default=lambda s: vars(s))


def base64_decode(str:str, output='utf-8'):
    ''' Decode a given string using Base 64 and output as UTF-8 string
    '''
    if output is None:
        return base64.b64decode(str)
    else:
        return base64.b64decode(str).decode('utf-8')


def base64_encode(str:str):
    ''' Encode a given string using Base64 by converting the string into bytes using UTF-8. Output as ASCII string.
    '''
    return base64.b64encode(bytes(str, 'utf-8')).decode('ascii')


def find_json_field(obj, field_names):
    if len(field_names) == 1:
        return obj.get(field_names[0]);
    
    field = field_names.pop(0)
    return find_json_field(obj.get(field), field_names)


def get_jira_key(branch_name: str):
    ''' Search for JIRA key in branch name using regular expression
    '''
    key = re.search("[A-Z]+-[0-9]+", branch_name)
    if key is not None:
        return key.group()
    
    return None