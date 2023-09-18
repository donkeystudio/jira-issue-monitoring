from configparser import ConfigParser
from datetime import datetime, timedelta
from helpers.api_caller_telegram import APICallerTelegram
from helpers.api_caller_jira import APICallerJIRA
import helpers.utils as utils
import logging
import sched
import time
import pytz
from server.end_points.request_report import RequestReport
from server.api_server import APIServer


class JIRAMonitor:
    ''' Monitor the following rules in JIRA:
    - Number of newly created issues added into an active sprint has exceeded a certain threshold compared to the number of issues at the start of the sprint.
    - Number of aged issues (unresolved after a certain number of days)
    - Number of issues that have been rolled over for more than a certain number of sprints.
    - Number of issues of which the summary contains a certain keywords and not yet resolved after a certain number of days.

    Rules are configured in a config file under a section named "MONITORING-RULES"
    '''
    
    SECTION="MONITORING-RULES"
    CONFIG_KEY="CONFIG"

    _config: None
    _logger = logging.getLogger(__name__)

    _jira_api_caller: APICallerJIRA
    _telegram_api_caller: APICallerTelegram

    time_scheduler  = sched.scheduler(time.time, time.sleep)
    scheduler_list  = []
    
    
    def __init__(self, config_file:str) -> None:
        config_parser = ConfigParser()
        config_parser.read(config_file)

        try:
            if config_parser.has_option(self.SECTION, self.CONFIG_KEY):
                self._config = utils.json_to_object(config_parser.get(self.SECTION, self.CONFIG_KEY))
                self._telegram_api_caller   = APICallerTelegram(self._config.telegram.config)
                self._jira_api_caller   = APICallerJIRA(self._config.jira.config)
            else:
                self._logger.fatal(f"CONFIG is NOT found under {self.SECTION} section")
        except:
            self._logger.fatal("Configuration setup failed!")


    def check_active_sprint(self, rule_config):
        '''  Monitor if number of newly created issues added into an active sprint has exceeded a certain threshold compared to the number of issues at the start of the sprint.
        '''

        jql_exclude_status = ""
        if len(rule_config.exclude_status) > 0:
            separator = ","
            jql_exclude_status = f'and status not in ({separator.join(rule_config.exclude_status)})'

        jql = f'filter = \"{rule_config.filter}\" {jql_exclude_status} and sprint in openSprints()'
        search_active_sprint = self._jira_api_caller.do_jira_search(jql, 1, 0, ["Sprint"])

        sprint_start_date = None
        sprint_name = None
        sprint_id   = None
        for issue in search_active_sprint.issues:
            sprint_start_date = datetime.strptime(vars(issue.fields).get(self._jira_api_caller.get_field('Sprint'))[0].startDate, '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%Y-%m-%d')
            sprint_name       = vars(issue.fields).get(self._jira_api_caller.get_field('Sprint'))[0].name
            sprint_id         = vars(issue.fields).get(self._jira_api_caller.get_field('Sprint'))[0].id

        total_issue_in_sprint = search_active_sprint.total

        if sprint_start_date is not None:
            jql = f'filter = \"{rule_config.filter}\" {jql_exclude_status} and sprint in openSprints() and createdDate > {sprint_start_date}'
            
            search_issue_added_after_sprint = self._jira_api_caller.do_jira_search(jql, 200, 0, ["issuetype"])
            total_per_types = {}
            for issue in search_issue_added_after_sprint.issues:
                issue_type = issue.fields.issuetype.name
                total = total_per_types.get(issue_type)
                if total == None:
                    total_per_types[issue_type] = 1
                else:
                    total_per_types[issue_type] = total + 1

            total_issue_added_after_sprint  = search_issue_added_after_sprint.total
            
            if total_issue_added_after_sprint >= total_issue_in_sprint * rule_config.threshold:
                output = f'Number of newly added tickets after the start of sprint [{sprint_name}]({self._jira_api_caller.create_jira_sprint_link(sprint_id)}) has exceeded {rule_config.threshold * 100}%. Total tickets at start of the sprint: {total_issue_in_sprint-total_issue_added_after_sprint}. Total newly added tickets: {total_issue_added_after_sprint}, which comprise of '
                type_detail = [f'{total_per_types[type]} {type}, ' for type in total_per_types]
                output += ', '.join(type_detail)
                return output
        
        return None


    def check_enquiry_sla(self, rule_config):
        ''' Monitor number of aged issues (unresolved after a certain number of days)
        '''
        
        jql_exclude_status = ""
        if len(rule_config.exclude_status) > 0:
            separator = ","
            jql_exclude_status = f'and status not in ({separator.join(rule_config.exclude_status)})'

        jql = f'filter = \"{rule_config.filter}\" {jql_exclude_status} and resolution = Unresolved and createdDate < startOfDay(-{rule_config.threshold})'
        
        search_result   = self._jira_api_caller.do_jira_search(jql, 100, 0, [""])
        total_enquiries = search_result.total

        if total_enquiries > 0:
            enquiry_list = [issue.key for issue in search_result.issues]
            return f'There are total {total_enquiries} [BAU enquiries]({self._jira_api_caller.create_jira_issues_link(enquiry_list)}) aged more than {rule_config.threshold} days.'
        
        return None
    

    def check_rollover_sprint(self, rule_config):
        ''' Monitor number of issues that have been rolled over for more than a certain number of sprints.
        '''
        
        jql_exclude_status = ""
        if len(rule_config.exclude_status) > 0:
            separator = ","
            jql_exclude_status = f'and status not in ({separator.join(rule_config.exclude_status)})'

        jql = f'filter = \"{rule_config.filter}\" {jql_exclude_status} and resolution = Unresolved and sprint in openSprints() and sprint in closedSprints()'
        search_result   = self._jira_api_caller.do_jira_search(jql, 100, 0, ["Sprint"])
        total_issues    = search_result.total

        if total_issues > 0:
            total_rollover = 0
            issue_list = []

            for issue in search_result.issues:
                sprints = vars(issue.fields).get(self._jira_api_caller.get_field('Sprint'))
                if len(sprints) >= rule_config.threshold:
                    total_rollover += 1
                    issue_list.append(issue.key)
    
            if total_rollover > 0:
                return f'There are total {total_rollover} unresolved [issues]({self._jira_api_caller.create_jira_issues_link(issue_list)}) that has been rolling over for more than {rule_config.threshold} sprints.'
        
        return None
    
    
    def check_keyword_sla(self, rule_config):
        ''' Monitor number of issues of which the summary contains a certain keyword and has not yet been resolved after a certain number of days.
        '''
        
        message = ""
        jql_exclude_status = ""
        if len(rule_config.exclude_status) > 0:
            separator = ","
            jql_exclude_status = f'and status not in ({separator.join(rule_config.exclude_status)})'

        jql = f'filter = \"{rule_config.filter}\" {jql_exclude_status} and resolution = Unresolved and summary ~ \"{rule_config.keyword}\" and createdDate < startOfDay(-{rule_config.threshold})'
        
        search_result = self._jira_api_caller.do_jira_search(jql, 100, 0, [""])
        total_issues = search_result.total

        if total_issues > 0:
            issue_list = [issue.key for issue in search_result.issues]
            message += f'There are total {total_issues} [issues]({self._jira_api_caller.create_jira_issues_link(issue_list)}) containing keyword \'{rule_config.keyword}\' not yet closed for more than {rule_config.threshold} days.'
        
        if len(message) > 0:
            return message

        return None
    

    def generate_report(self, project_id = None):
        message = ""
        
        for project_config in self._config.rules.projects:
            if project_id is not None and project_id != project_config.id:
                continue

            project_name = project_config.name
            status_messages = []
            for rule_config in project_config.rules:
                if rule_config.id == "added_active_sprint":
                    status_messages.append(self.check_active_sprint(rule_config))
                elif rule_config.id == "enquiry_sla":
                    status_messages.append(self.check_enquiry_sla(rule_config))
                elif rule_config.id == "sprint_rollover":
                    status_messages.append(self.check_rollover_sprint(rule_config))
                elif rule_config.id == "keyword_sla":
                    status_messages.append(self.check_keyword_sla(rule_config))

            #Construct message only if there's a rule found for current project
            if len(project_config.rules) > 0:
                message += f'\n*{project_name}*\n'
                status_messages = [status for status in status_messages if status is not None]

                if len(status_messages) == 0:
                    message += "Everything looks good.\n"
                else:
                    for status in status_messages:
                        message += f'- {status}\n'

        if len(message) > 0:
            header_message = f'JIRA REPORT _({datetime.today().strftime("%d/%m/%Y")})_\n' \
                                "=====================\n"
            return header_message + message
        
        return message

    def start_monitoring(self):
        message = self.generate_report()
        
        if message:
            self._telegram_api_caller.send_telegram_message(message)

        #Schedule for the next reprt
        self.scheduler_list.append(self.time_scheduler)


    def schedule_next_report(self, scheduler: sched.scheduler):
        time_now = datetime.now()
        sorted_day_list = self._config.frequency.day_of_week
        sorted_day_list.sort()
        sorted_hour_list= self._config.frequency.hour_of_day
        sorted_hour_list.sort()

        next_schedule_time: datetime
        next_schedule_time = None

        available_hours = [hour for hour in sorted_hour_list if hour > time_now.hour]
        available_hours.sort()
        available_wkday = [wkday for wkday in sorted_day_list if wkday > time_now.weekday()]
        available_wkday.sort()

        if time_now.weekday() in sorted_day_list and len(available_hours) > 0:
            next_schedule_time = datetime.strptime(f'{time_now.day}-{time_now.month}-{time_now.year} {available_hours[0]}:00:00', '%d-%m-%Y %H:%M:%S')
        elif len(available_wkday) > 0:
            next_schedule_time = datetime.strptime(f'{time_now.day}-{time_now.month}-{time_now.year} {sorted_hour_list[0]}:00:00', '%d-%m-%Y %H:%M:%S')+timedelta(days=available_wkday[0] - time_now.weekday())
        else:
            next_schedule_time = datetime.strptime(f'{time_now.day}-{time_now.month}-{time_now.year} {sorted_hour_list[0]}:00:00', '%d-%m-%Y %H:%M:%S')+timedelta(days=sorted_day_list[0] - time_now.weekday() + 7)

        delay = (next_schedule_time.astimezone(pytz.utc) - time_now.astimezone(pytz.utc)).total_seconds()
        self._logger.info(f'Today date is:{time_now.strftime("%d-%m-%Y %H:%M")}. Next report is scheduled at:{next_schedule_time.strftime("%d-%m-%Y %H:00")}')
        scheduler.enter(delay,1, self.start_monitoring)
        scheduler.run()
    

    def monitor_scheduler(self):
        while True:
            if len(self.scheduler_list) > 0:
                self.schedule_next_report(self.scheduler_list.pop())


    def run(self):
        #Check if should run now
        time_now = datetime.now()

        if time_now.weekday() in self._config.frequency.day_of_week and time_now.hour in self._config.frequency.hour_of_day :
            self.start_monitoring()
        else:
            self.scheduler_list.append(self.time_scheduler)

        #Start Monitoring
        self.monitor_scheduler()
    

    def start_api_server(self, port, log_level):
        request_report = RequestReport([self._config.adhoc_request, self.generate_report])
        server = APIServer("Jira Report API Server")
        server.add_resource(request_report, '/report/jira', [self._config.adhoc_request, self.generate_report])
        server.start('0.0.0.0', port, debug=log_level.upper()==logging.getLevelName(logging.DEBUG))
