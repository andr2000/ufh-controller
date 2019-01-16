import logging
import os
import sqlite3
import time

import config


class Database(object):
    __instance = None

    def __new__(cls):
        if Database.__instance is None:
            Database.__instance = object.__new__(cls)
            Database.__instance.logger = logging.getLogger(__name__)
            Database.__instance.__initialized = False
        return Database.__instance

    def __del__(self):
        self.logger.info('Done')

    @classmethod
    def destroy(cls):
        del cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        self.logger.info('Openning the database')
        cfg = config.Config()
        self.db_file = self.expand_path(cfg.db_get_database_file())
        if not os.path.isfile(self.db_file):
            sql_file = self.expand_path(cfg.db_get_schema_file())
            self._create(self.db_file, sql_file)

    @staticmethod
    def expand_path(path):
        return os.path.normpath(os.path.expandvars(os.path.expanduser(path)))

    @staticmethod
    def parse_frac(val, power):
        l = len(val)
        dotpos = val.find('.')
        if dotpos == -1:
            return int(val) * (10 ** power)

        i, _, f = val.partition(".")

        if len(f) > power:
            l -= len(f) - power
            f = f[:power]

        return int(i + f) * (10 ** (power - (l - dotpos - 1)))

    def _create(self, db_file, sql_file):
        self.logger.info ('Creating database at %s using schema %s' %
                (db_file, sql_file))
        try:
            fd = open(sql_file, 'r')
            script = fd.read()
            db = sqlite3.connect(db_file)
            cur = db.cursor()
            cur.executescript(script)
        except OSError as e:
            self.logger.error(str(e))

    def store_boiler(self, values):
        try:
            vals = []
            vals.append(int(time.time()))
            vals.append(self.parse_frac(values['FlowTempDesired'], 2))
            vals.append(self.parse_frac(values['FlowTemp'], 2))
            vals.append(values['FlowTemp_sensor'])
            vals.append(self.parse_frac(values['ReturnTemp'], 2))
            vals.append(values['ReturnTemp_sensor'])
            vals.append(values['Flame'])
            vals.append(self.parse_frac(values['PowerPercent'], 2))
            vals.append(self.parse_frac(values['WaterPressure'], 3))
            vals.append(self.parse_frac(values['PumpPower'], 2))
            vals.append(values['Status01'])
            vals.append(values['Status02'])
            vals.append(values['SetModeR'])
            SQL = (
                'INSERT INTO boiler (datetime_unix,'
                'temp_flow_target_100,temp_flow_100,temp_flow_sensor,'
                'temp_return_100,temp_return_sensor,'
                'flame_state,power_hc_percent_100,water_pressure_1000,'
                'power_pump_100,status01,status02,set_mode_r) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)'
            )
            with sqlite3.connect(self.db_file) as con:
                con.execute(SQL, vals)
                con.commit()
        except sqlite3.IntegrityError:
            self.logger.error('Could not insert into boiler')
        except Exception as e:
            self.logger.error(str(e))
