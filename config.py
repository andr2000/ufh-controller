import argparse
import logging

log = logging.getLogger(__name__)

__args = None
options = {}


def __init_config():
    global __args
    global options

    log.info('Reading configuration')
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='config_file', required=False,
                        help="Use configuration file for tuning")
    __args = parser.parse_args()
    # TODO: Eventually the below will be read from the config file and
    # command line arguments.
    options['ebusd_address'] = 'localhost'
    options['ebusd_port'] = 8888
    options['daemonize'] = False
    options['db_database_file'] = '${PWD}/ufh-controller.db'
    options['db_schema_file'] = '${PWD}/schema.sql'


__init_config()
