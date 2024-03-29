# Jira Issue Monitoring
Periodically monitor Jira based on certain rules. There are few ways to access the report:
* Periodically send to Telegram chat.
* Access via API.

## List of Supported Rules
| Rule ID | Description | Threshold Unit |
| :--- | :--- | :--- |
| `added_active_sprint` | Monitor if number of newly created issues added into an active sprint has exceeded a certain threshold compared to the number of issues at the start of the sprint. | Percentage. Between 0 to 1 (e.g. 0.1 as 10%) |
| `enquiry_sla` | Monitor number of aged issues (unresolved after a certain number of days) | Day(s) |
| `sprint_rollover` | Monitor number of issues that have been rolled over for more than a certain number of sprints. | Number of Sprint(s) |
| `keyword_sla` | Monitor number of issues of which the summary contains a certain keyword and has not yet been resolved after a certain number of days. | Day(s) |

## [Docker](https://hub.docker.com/r/donkeystudio/jira-issue-monitoring)
Supported architectures: `linux/arm/v7`, `linux/arm64`, `linux/amd64`

## Startup Configuration
```bash
python3 main.py --help
usage: main.py [-h] [-conf CONFIG_FILE] [-log LOG_FILE] [-d DEBUG_LEVEL]

options:
  -h,                   --help                      show this help message and exit
  -conf CONFIG_FILE,    --config_file CONFIG_FILE   Location of the application config file (default: ./config.properties)
  -p PORT,              --port PORT                 Port of the API service (default: 8080)
  -log  LOG_FILE,       --log_file LOG_FILE         Location of the log file. Default is system log (default: None)
  -d    DEBUG_LEVEL,    --debug_level DEBUG_LEVEL   Debug Level CRITICAL/ERROR/WARNING/INFO/DEBUG. Default is WARNING (default: WARNING)
```

## Configuration File
ID and API Key are encoded using Base64 encoding.

### Jira configuration section
```json
[JIRA-API]
CONFIG={
    "url":<Jira URL>,
    "id":<Jira account (Email address). Base64 encoded.>,
    "key":<Jira API Token. Base64 encoded>,
    "field_mapping":{
        "Sprint":<field name of Sprint on your Jira. In some Jira system, Sprint is stored as customfield_XXXXXX>
        }
    }
```

### Telegram configuration section
```json
[TELEGRAM-API]
CONFIG={
    "url":"https://api.telegram.org",
    "chat_id":<id of the targetting Telegram chat. Base64 encoded.>,
    "bot_token":<Your Telegram Bot token. Base64 encoded.>
    }
```

### Rule monitoring configuration section
```json
[MONITORING-RULES]
CONFIG={
        "frequency":
        {
            "day_of_week":
            [
                <Days of the week to trigger the report. Monday is 0. Sunday is 6>
            ],
            "hour_of_day":
            [
                <Hours of the day to trigger the report. From 0 to 23>
            ]
        },
        "rules":
        {
            "projects":
            [
                {
                    "id":<Project ID>,
                    "name":<Project Name>,
                    "rules":
                    [
                        {
                            "id":<Rule ID>,
                            "threshold": <Rule Threshold. See List of Supported Rules for threshold unit>,
                            "filter":<Name of the filter on Jira that you want to use to monitor this rule>,
                            "exclude_status":
                            [
                                <List of workflow status you want to exclude from your monitoring>
                            ],
                            "keyword":<Keyword to monitor. Only applicable for rule "keyword_sla">
                        }
                    ]
                }
            ]
        },
        "jira":
        {
            "config": <Required. Path to Jira configuration file.>
        },
        "telegram":
        {
            "config": <Required. Path to Telegram Config>
        },
        "adhoc_request":
        {
            "api_key":
            {
                "key": <Required. API Key of the service. In Base64 encoded format. Leave empty string if API Key is disabled.>,
                "header": <Required. Header field where the API Key is stored. Leave empty string if API Key is disabled.>
            },
            ....
        }
    }
```
## API Services
### `/report/jira`
```http
POST /report/jira
```
Check and return a comment with a list of potential conflict pull requests.

**Authentication**: API Key. Refer to [MONITORING-RULES] config section -> `adhoc_request`.

**JSON Request Body**
```json
{
    "project": <Optional. Project ID. String type. Contains only alphabet characters. If no project is passed, report will be generated for all configured projects.>
}
```

**Example**
```json
[MONITORING-RULES]
CONFIG={
        "frequency":
        {
            "day_of_week":
            [
                0, 3
            ],
            "hour_of_day":
            [
                8, 18
            ]
        },
        "rules":
        {
            "projects":
            [
                {
                    "id":PRJ_1,
                    "name":Project Zero,
                    "rules":
                    [
                        {
                            "id":"added_active_sprint",
                            "threshold": 0.1,
                            "filter":"Filter for PRJ 1",
                            "exclude_status":
                            [
                                "Rejected"
                            ]
                        },
                        {
                            "id":"enquiry_sla",
                            "threshold":14,
                            "filter":"Filter for PRJ 1 - New version",
                            "exclude_status":
                            [
                                "Closed"
                            ]
                        },
                        {
                            "id":"sprint_rollover",
                            "threshold": 4,
                            "filter":"Filter for PRJ 1",
                            "exclude_status":
                            []
                        },
                        {
                            "id":"keyword_sla",
                            "threshold": 2,
                            "filter":"Filter for PRJ 1",
                            "exclude_status":
                            [],
                            "keyword":"CRITICAL"
                        }
                    ]
                }
            ]
        },
        "jira":
        {
            "config": "./config.properties"
        },
        "telegram":
        {
            "config": "./config.properties"
        },
        "adhoc_request":
        {
            "api_key":
            {
                "key": "MTIzMzQ1Ng==", //123456
                "header": "APIKey"
            },
            "request_schema":
            {
                "type" : "object",
                "properties" :
                {
                    "project":
                    {
                        "type" : "string",
                        "pattern": "^([A-Za-z])+$"
                    }
                }
            }
        }
    }
```
**Explanation**

In the above example, `Project Zero` will be monitored with the following rules:
1. Monitor all issues from `Filter for PRJ 1`, excluding those with status `Rejected`. If number of newly created issues added into an active sprint exceeded `10%` of total number of issues at the start of the sprint, alert will be triggered.
2. Monitor all issues from `Filter for PRJ 1 - New version`, excluding those with status `Closed`. If there is any issue not yet resolved for more than `14 days`, alert will be triggered.
3. Monitor all issues from `Filter for PRJ 1`. If there is any issue that has been rolled over to at least `4 sprints`, including the current active sprint, alert will be triggered.
4. Monitor all issues from `Filter for PRJ 1`. If there is any issue of which summary contains keyword `Critical` and has not yet been resolved for more than `2 days`, alert will be triggered.

Delivery of the report:
* Alert will be triggered every `Monday` and `Thursday` at `8AM` and `6PM`.
* Accesible via http://localhost:8080/report/jira with API Key with header field `APIKey` and key `123456` 