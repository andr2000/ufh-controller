import logging
import time

import config
import ebus
import version


logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)


def main():
    ebus_devs = None

    try:
        logger.info('This is %s v%s' % (version.PRODUCT, version.VERSION))

        ebus_devs = ebus.Ebus()
        ebus_devs.start()

        if config.options['daemonize']:
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
