import database
import logging
import http.client
import re
import ssl
import telegram
import time
import urllib.parse


logger = logging.getLogger(__name__)

temperature = {}
timestamp = None


def get_sinoptik():
    WEATHER_PROVIDER = 'ua.sinoptik.ua'

    logger.debug('Connecting to %s' % WEATHER_PROVIDER)
    buffer = b''
    try:
        conn = http.client.HTTPSConnection(WEATHER_PROVIDER)
        conn.request('GET', '/' + urllib.parse.quote_plus('погода-глеваха'),
                headers={'User-Agent' : ''})
        resp = conn.getresponse()
        if resp.status != 200:
            logger.error('Failed to connect to ' + WEATHER_PROVIDER + ':' +
                    resp.reason)
            return
        buffer = str(resp.read())
    except (ssl.SSLError, http.client.HTTPException, OSError) as e:
        logger.error(str(e))
        return

    result = {}
    # Parse current temperature.
    pattern = re.compile(r'<p class="today-temp">.*?([+-]?\d+).*</p>')
    result['t_now'] = re.findall(pattern, buffer)[0]

    # Read temperatures forecast per hour.
    vals = []
    pattern = re.compile(r'<tr class="temperature">(.+?)</tr>')
    res = re.findall(pattern, buffer)
    if res and len(res):
        res_split = res[0].split('> <')
        pattern = re.compile(r'>.*?([+-]?\d+).*<')
        for t in res_split:
            vals.append(re.findall(pattern, t)[0])
    result['forecast_hourly'] = vals

    # Read feels like temperatures per hour.
    vals = []
    pattern = re.compile(r'<tr class="temperatureSens">(.+?)</tr>')
    res = re.findall(pattern, buffer)
    if res and len(res):
        res_split = res[0].split('> <')
        pattern = re.compile(r'>.*?([+-]?\d+).*<')
        for t in res_split:
            vals.append(re.findall(pattern, t)[0])
    result['forecast_feels_like_hourly'] = vals

    # Read hour stamps for hour's temperatures.
    vals = []
    pattern = re.compile(r'<tr class="gray time">(.+?)</tr>')
    res = re.findall(pattern, buffer)
    if res and len(res):
        res_split = res[0].split('> <')
        pattern = re.compile(r'>(.*)<')
        for t in res_split:
            # Remove all whitespace and parse
            vals.append(re.findall(pattern, ''.join(t.split()))[0])
    result['forecast_time_range_hourly'] = vals

    # Read day forecast: min temperature by day.
    vals = []
    pattern = re.compile(r'<div class="min">(.+?)</div>')
    res = re.findall(pattern, buffer)
    if res:
        pattern = re.compile('<span>.*?([+-]?\d+).*</span>')
        for t in res:
            vals.append(re.findall(pattern, t)[0])
    result['forecast_low_7day'] = vals

    # Read day forecast: max temperature by day.
    vals = []
    pattern = re.compile(r'<div class="max">(.+?)</div>')
    res = re.findall(pattern, buffer)
    if res:
        pattern = re.compile(r'<span>.*?([+-]?\d+).*</span>')
        for t in res:
            v= re.findall(pattern, t)[0]
            vals.append(v)
    result['forecast_high_7day'] = vals

    return result


def get_sinoptik_cur_hour_index(ts):
    # Sinoptik's result also has hourly values and the corresponding
    # time ranges as strings. Find the index which corresponds to the
    # time given
    if not temperature['forecast_time_range_hourly']:
        return -1

    try:
        # Convert the timestamp to struct_time, so we can have hour and
        # minutes
        tm = time.localtime(ts)
        tm_ranges = temperature['forecast_time_range_hourly']
        idx = len(tm_ranges) - 1
        for t in reversed(tm_ranges):
            hour, minutes = t.split(':')
            t = time.mktime((tm.tm_year, tm.tm_mon, tm.tm_mday,
                             int(hour), int(minutes), 0, 0, 0, 0))
            if (t <= timestamp):
                break
            idx -= 1
    except (IndexError, ValueError):
        return -1

    return idx


def process():
    global temperature
    global timestamp

    temperature = {}
    timestamp = None

    try:
        temperature = get_sinoptik()
    except (IndexError, ValueError):
        return

    if not temperature:
        return

    timestamp = time.time()

    logger.debug(temperature)

    hour_idx = get_sinoptik_cur_hour_index(timestamp)
    # store to the database
    try:
        if hour_idx < 0:
            t_feels_like = ''
        else:
            t_feels_like = temperature['forecast_feels_like_hourly'][hour_idx]

        values = {
            'T_sinoptik': temperature['t_now'],
            'T_sinoptik_feels_like': t_feels_like
        }
        database.store_weather(values)
        telegram.send_message('Toutside ' + temperature['t_now'] +
                              ' feels like ' + t_feels_like)
    except (ValueError, IndexError) as e:
        logger.error(str(e))

process()
