import logging
import http.client
import re
import urllib.parse


logger = logging.getLogger(__name__)


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
    except http.client.HTTPException as e:
        logger.error(str(e))
        return

    result = {}
    # Parse current temperature.
    pattern = re.compile(r'<p class="today-temp">(.[+-]?\d+).*</p>')
    result['t_now'] = re.findall(pattern, buffer)

    # Read temperatures forecast per hour.
    vals = []
    pattern = re.compile(r'<tr class="temperature">(.+?)</tr>')
    res = re.findall(pattern, buffer)
    if res and len(res):
        res_split = res[0].split('> <')
        pattern = re.compile(r'>(.[+-]?\d+).*<')
        for t in res_split:
            vals.append(re.findall(pattern, t))
    result['forecast_hourly'] = vals

    # Read feels like temperatures per hour.
    vals = []
    pattern = re.compile(r'<tr class="temperatureSens">(.+?)</tr>')
    res = re.findall(pattern, buffer)
    if res and len(res):
        res_split = res[0].split('> <')
        pattern = re.compile(r'>(.[+-]?\d+).*<')
        for t in res_split:
            vals.append(re.findall(pattern, t))
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
            vals.append(re.findall(pattern, ''.join(t.split())))
    result['forecast_time_range_hourly'] = vals

    # Read day forecast: min temperature by day.
    vals = []
    pattern = re.compile(r'<div class="min">(.+?)</div>')
    res = re.findall(pattern, buffer)
    if res:
        pattern = re.compile(r'<span>(.[+-]?\d+).*</span>')
        for t in res:
            vals.append(re.findall(pattern, t))
    result['forecast_low_7day'] = vals

    # Read day forecast: max temperature by day.
    vals = []
    pattern = re.compile(r'<div class="max">(.+?)</div>')
    res = re.findall(pattern, buffer)
    if res:
        pattern = re.compile(r'<span>(.[+-]?\d+).*</span>')
        for t in res:
            vals.append(re.findall(pattern, t))
    result['forecast_high_7day'] = vals

    return result

