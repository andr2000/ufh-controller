import argparse
import logging


class Config(object):
    __instance = None

    def __new__(cls):
        if Config.__instance is None:
            Config.__instance = object.__new__(cls)
            Config.__instance.logger = logging.getLogger(__name__)
            Config.__instance.__parse_args()
        return Config.__instance

    def __parse_args(self):
        self.logger.info('Reading configuration')
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', dest='config_file', required=False,
                            help="Use configuration file for tuning")
        self.__args = parser.parse_args()

    def ebusd_address(self):
        return 'localhost'

    def ebusd_port(self):
        return 8888

    def daemonize(self):
        return False

    def db_get_database_file(self):
        return '/tmp/vaillant.db'

    def db_get_schema_file(self):
        return '${PWD}/schema.sql'

