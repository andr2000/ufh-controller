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
import version
import weather


def main():
    ebus_devs = None

    try:
        logger.info('This is %s v%s' % (version.PRODUCT, version.VERSION))

        ebus_devs = ebus.Ebus()
        ebus_devs.start()

        if config.options['daemonize']:
            logger.info('Running as daemon')
            pass
        else:
            while True:
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


if __name__ == '__main__':
    main()
