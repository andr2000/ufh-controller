import logging
import os
import sqlite3
import time

import config

logger = logging.getLogger(__name__)

db_file = ''


def expand_path(path):
    return os.path.normpath(os.path.expandvars(os.path.expanduser(path)))


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


def create(db_file, schema_file):
    logger.info('Creating database at %s using schema %s' % (db_file, schema_file))
    try:
        logger.debug(os.path.dirname(db_file))
        os.makedirs(os.path.dirname(db_file))
    except OSError as e:
        if e.errno != os.errno.EEXIST:
            raise
    try:
        fd = open(schema_file, 'r')
        script = fd.read()
        db = sqlite3.connect(db_file)
        cur = db.cursor()
        cur.executescript(script)
    except OSError as e:
        logger.error(str(e))
        raise


def store_boiler(values):
    try:
        row = []
        row.append(int(time.time()))
        row.append(parse_frac(values['FlowTempDesired'], 2))
        row.append(parse_frac(values['FlowTemp'], 2))
        row.append(values['FlowTemp_sensor'])
        row.append(parse_frac(values['ReturnTemp'], 2))
        row.append(values['ReturnTemp_sensor'])
        row.append(values['Flame'])
        row.append(parse_frac(values['PowerPercent'], 2))
        row.append(parse_frac(values['WaterPressure'], 3))
        row.append(parse_frac(values['PumpPower'], 2))
        row.append(values['Status01'])
        row.append(values['Status02'])
        row.append(values['SetModeR'])
        SQL = (
            'INSERT INTO boiler (datetime_unix,'
            'temp_flow_target_100,temp_flow_100,temp_flow_sensor,'
            'temp_return_100,temp_return_sensor,'
            'flame_state,power_hc_percent_100,water_pressure_1000,'
            'power_pump_100,status01,status02,set_mode_r) '
            'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)'
        )
        with sqlite3.connect(db_file) as con:
            con.execute(SQL, row)
            con.commit()
    except sqlite3.IntegrityError:
        logger.error('Could not insert into boiler')
    except ValueError as e:
        logger.error(str(e))


def store_vrc700f(values):
    try:
        row = []
        row.append(int(time.time()))
        row.append(parse_frac(values['FlowTempDesired'], 2))
        row.append(parse_frac(values['RoomTempDesired'], 2))
        row.append(parse_frac(values['RoomTemp'], 2))
        row.append(parse_frac(values['DayTemp'], 2))
        row.append(parse_frac(values['NightTemp'], 2))
        row.append(parse_frac(values['OutTemp'], 2))
        row.append(values['RecLvlHead'])
        row.append(values['RecLvlOut'])
        SQL = (
            'INSERT INTO vrc700 (datetime_unix,'
            'temp_flow_des_100,temp_room_des_100,temp_room_100,'
            'temp_day_100,temp_night_100,temp_out_100,'
            'rec_lvl_head,rec_lvl_out) '
            'VALUES (?,?,?,?,?,?,?,?,?)'
        )
        with sqlite3.connect(db_file) as con:
            con.execute(SQL, row)
            con.commit()
    except sqlite3.IntegrityError:
        logger.error('Could not insert into vrc700')
    except ValueError as e:
        logger.error(str(e))


def store_weather(values):
    try:
        row = []
        row.append(int(time.time()))
        row.append(parse_frac(values['T_sinoptik'], 1))
        row.append(parse_frac(values['T_sinoptik_feels_like'], 1))
        SQL = 'INSERT INTO weather (datetime_unix,t_sinoptik_10,'\
              't_sinoptik_feels_like_10) VALUES (?,?,?)'
        with sqlite3.connect(db_file) as con:
            con.execute(SQL, row)
            con.commit()
    except sqlite3.IntegrityError:
        logger.error('Could not insert into weather')
    except ValueError as e:
        logger.error(str(e))


def __init_database():
    global db_file

    db_file = expand_path(config.options['db_database_file'])
    logger.info('Openning the database at %s', db_file)
    if not os.path.isfile(db_file):
        schema_file = expand_path(config.options['db_schema_file'])
        create(db_file, schema_file)


__init_database()
