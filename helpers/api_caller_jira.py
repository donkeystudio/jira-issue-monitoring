from urllib.parse import quote
from helpers.api_caller import APICaller
import helpers.utils as utils

class APICallerJIRA(APICaller):
    
    URL_JIRA_SEARCH   = "/rest/api/3/search"
    SECTION = "JIRA-API"


    def __init__(self, config_file) -> None:
        super().__init__(config_file)


    def get_header(self):
       return f'{utils.base64_decode(self._config.id)}:{utils.base64_decode(self._config.key)}'

    
    def get_field(self, field:str):
        return getattr(self._config.field_mapping, field)
    

    ########## Specific calls to Jira REST API ##########
    def do_jira_search (self, jql:str, max:int, start=0, fields = []):
        
        mapped_fields = [getattr(self._config.field_mapping, key) if len(key) > 0 and hasattr(self._config.field_mapping, key) else key for key in fields]
        
        if len(mapped_fields) == 0:
            mapped_fields.append("")

        json_body = {
            "fields": mapped_fields,
            "fieldsByKeys": False,
            "jql": jql,
            "maxResults": max,
            "startAt": start
        }

        return self.do_post(self.URL_JIRA_SEARCH, json_body)
    
    
    def create_jira_issues_link(self, issues = []):
        if len(issues) == 0:
            return None
        
        separator = ","
        url = self.construct_url("/issues")
        query = f'?jql=issuekey in ({separator.join(issues)})'
        url += quote(query)

        return url
    

    def create_jira_sprint_link(self, sprint_id):
        url = self.construct_url("/issues")
        query = f'?jql=sprint={sprint_id}'
        url += quote(query)

        return url
