import logging
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from threading import Thread
from monitor import JIRAMonitor

# Parse command line arguments
parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-conf", "--config_file", default="./config.properties", help="Location of the application config file")
parser.add_argument("-p", "--port", default=8080, type=int, help="Port")
parser.add_argument("-log", "--log_file", default=None, type=str, help="Location of the log file. Default is system log")
parser.add_argument("-d", "--debug_level", default="WARNING", type=str, help="Debug Level CRITICAL/ERROR/WARNING/INFO/DEBUG. Default is WARNING")
args = vars(parser.parse_args())

PORT      = args["port"]
CONF_FILE = args["config_file"]
LOG_FILE  = args["log_file"]
LOG_LEVEL = args["debug_level"]


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_FILE, format='%(asctime)s %(levelname)s [%(name)s] %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level = LOG_LEVEL.upper())

    monitor = JIRAMonitor(CONF_FILE)
    Thread(target=monitor.run).start()
    Thread(target=monitor.start_api_server, args=[PORT, LOG_LEVEL]).start()
    