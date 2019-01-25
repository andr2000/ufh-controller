import logging
logger = logging.getLogger()
import time

import config
LOGGER_FMT_TIMESTAMP = '%m-%d-%y %H:%M:%S'
LOGGER_FMT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
if config.options['logfile']:
    logging.basicConfig(level=config.options['loglevel'],
                        datefmt=LOGGER_FMT_TIMESTAMP,
                        format=LOGGER_FMT,
                        filename=config.options['logfile'])
else:
    logging.basicConfig(level=config.options['loglevel'],
                        datefmt=LOGGER_FMT_TIMESTAMP,
                        format=LOGGER_FMT)

import ebus
import telegram
import version
import weather

# Once half an hour.
WEATHER_POLL_TO_SEC = 30 * 60

def main():
    ebus_devs = None

    try:
        logger.info('This is %s v%s' % (version.PRODUCT, version.VERSION))
        telegram.send_message('Starting %s v%s' % (version.PRODUCT,
                                                   version.VERSION))

        ebus_devs = ebus.Ebus()
        ebus_devs.start()

        weather_till_run = 0
        if config.options['daemonize']:
            logger.info('Running as daemon')
            pass
        else:
            while True:
                weather_till_run += 1
                if weather_till_run > WEATHER_POLL_TO_SEC:
                    weather_till_run = 0
                    weather.process()
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
        telegram.send_message('<<<<<<Exiting>>>>>>')


if __name__ == '__main__':
    main()
