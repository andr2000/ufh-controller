#!/usr/bin/env python3

import logging
import logging.handlers
logger = logging.getLogger()
import time

import config

log_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
logger.setLevel(config.options['loglevel'])

if config.options['foreground']:
    log_console_handler = logging.StreamHandler()
    log_console_handler.setFormatter(log_formatter)
    logger.addHandler(log_console_handler)

if config.options['logfile']:
    log_file_handler = logging.handlers.RotatingFileHandler(
        config.options['logfile'],
        maxBytes=(1024 * 1024),
        backupCount=7
    )
    log_file_handler.setFormatter(log_formatter)
    logger.addHandler(log_file_handler)


import ebus
import telegram
import version
import weather

# Once half an hour.
WEATHER_POLL_TO_SEC = 30 * 60

TELEGRAM_POLL_TO_SEC = 5

def main():
    ebus_devs = None

    try:
        logger.info('This is %s v%s' % (version.PRODUCT, version.VERSION))
        telegram.send_message_now('Starting %s v%s' % (version.PRODUCT,
                                                       version.VERSION))

        ebus_devs = ebus.Ebus()
        ebus_devs.start()

        weather_till_run = 0
        telegram_till_run = 0
        if not config.options['foreground']:
            logger.info('Running as daemon')
            pass
        else:
            while True:
                weather_till_run += 1
                if weather_till_run > WEATHER_POLL_TO_SEC:
                    weather_till_run = 0
                    weather.process()
                telegram_till_run += 1
                if telegram_till_run > TELEGRAM_POLL_TO_SEC:
                    telegram_till_run = 0
                    telegram.process()
                time.sleep(1)
    finally:
        if ebus_devs:
            try:
                ebus_devs.stop()
                ebus_devs.join()
            except RuntimeError:
                pass
            del ebus_devs
        logger.info('Done')
        telegram.send_message_now('<<<<<<Exiting>>>>>>')


if __name__ == '__main__':
    main()