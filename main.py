import logging
from helpers.api_caller_jira import APICallerJIRA
from helpers.api_caller_telegram import APICallerTelegram
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from monitor import JIRAMonitor

# Parse command line arguments
parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-conf", "--config_file", default="./config.properties", help="Location of the application config file")
parser.add_argument("-log", "--log_file", default=None, type=str, help="Location of the log file. Default is system log")
parser.add_argument("-d", "--debug_level", default="WARNING", type=str, help="Debug Level CRITICAL/ERROR/WARNING/INFO/DEBUG. Default is WARNING")
args = vars(parser.parse_args())

CONF_FILE = args["config_file"]
LOG_FILE  = args["log_file"]
LOG_LEVEL = args["debug_level"]


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_FILE, format='%(asctime)s %(levelname)s [%(name)s] %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level = LOG_LEVEL.upper())

    #API Caller
    jira_api_caller     = APICallerJIRA(CONF_FILE)
    telegram_api_caller = APICallerTelegram(CONF_FILE)

    monitor = JIRAMonitor(CONF_FILE, CONF_FILE, CONF_FILE)
    monitor.run()
    