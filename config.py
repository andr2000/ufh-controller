import argparse
import configparser
import logging


class Config(object):
    __instance = None

    def __new__(cls):
        if Config.__instance is None:
            Config.__instance = object.__new__(cls)
            Config.__instance.__parse_args()
        return Config.__instance

    def __parse_args(self):
        logging.info('Reading configuration')
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', dest='config_file', required=False,
                            help="Use configuration file for tuning")
        self.__args = parser.parse_args()
