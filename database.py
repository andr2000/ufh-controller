import logging
import os
import sqlite3

import config


class Database(object):
    __instance = None

    def __new__(cls):
        if Database.__instance is None:
            Database.__instance = object.__new__(cls)
            Database.__instance.logger = logging.getLogger(__name__)
        return Database.__instance

    def __del__(self):
        self.logger.info('Done')

    @classmethod
    def destroy(cls):
        del cls.__instance

    def __init__(self):
        self.logger.info('Openning database')
        cfg = config.Config()
        db_file = self.expand_path(cfg.db_get_database_file())
        if not os.path.isfile(db_file):
            sql_file = self.expand_path(cfg.db_get_schema_file())
            self._create(db_file, sql_file)

    @staticmethod
    def expand_path(path):
        return os.path.normpath(os.path.expandvars(os.path.expanduser(path)))

    def _create(self, db_file, sql_file):
        self.logger.info ('Creating database at %s using schema %s' %
                (db_file, sql_file))

