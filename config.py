import argparse
import configparser
import logging
import os

logger = logging.getLogger(__name__)

options = {}


def expand_path(path):
    return os.path.normpath(os.path.expandvars(os.path.expanduser(path)))


CFG_SECTION_CORE = 'core'
CFG_OPTION_CORE_LOGLEVEL = 'loglevel'
CFG_OPTION_CORE_DAEMONIZE = 'daemonize'

CFG_SECTION_EBUSD = 'ebusd'
CFG_OPTION_EBUSD_ADDRESS = 'address'
CFG_OPTION_EBUSD_PORT = 'port'

CFG_SECTION_DATABASE = 'database'
CFG_OPTION_DATABASE_FILE = 'db_file'
CFG_OPTION_DATABASE_SCHEMA_FILE = 'schema_file'

def strip_quotes(val):
    return val.strip('"').strip("'")

def parse_config(cfg_file):
    global options

    full_path = expand_path(cfg_file)
    logger.info('Configuration file at ' + full_path)
    if not os.path.isfile(full_path):
        raise ValueError('Configuration file does not exist')
    config = configparser.ConfigParser()
    config.read(full_path)
    # Read 'core' section
    loglevel = config.get(CFG_SECTION_CORE, CFG_OPTION_CORE_LOGLEVEL,
                          fallback='info')
    if loglevel:
        d = {
            'error' : logging.ERROR,
            'warning' : logging.WARN,
            'info' : logging.INFO,
            'debug' : logging.DEBUG
        }
        options['loglevel'] = d[str(loglevel).lower()]
    options['daemonize'] = config.getboolean(CFG_SECTION_CORE,
            CFG_OPTION_CORE_DAEMONIZE, fallback=True)

    # Read 'ebusd' section
    options['ebusd_address'] = strip_quotes(config.get(CFG_SECTION_EBUSD,
                                                       CFG_OPTION_EBUSD_ADDRESS,
                                                       fallback='localhost'))
    options['ebusd_port'] = config.getint(CFG_SECTION_EBUSD,
                                          CFG_OPTION_EBUSD_PORT,
                                          fallback=8888)

    # Read 'database' section
    options['db_database_file'] = strip_quotes(config.get(CFG_SECTION_DATABASE,
                                                          CFG_OPTION_DATABASE_FILE,
                                                          fallback='${PWD}/ufh-controller.db'))
    options['db_schema_file'] = strip_quotes(config.get(CFG_SECTION_DATABASE,
                                                        CFG_OPTION_DATABASE_FILE,
                                                        fallback='${PWD}/schema.sql'))


def __init_config():
    global options

    logger.info('Reading configuration')
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=False,
                        help="Use configuration file for tuning")
    args = parser.parse_args()
    if args.config:
        parse_config(args.config)


__init_config()
