import logging
import time

import config
import database
import ebus_client
import version


def main():
    ebus = None
    db = None

    try:
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info('This is %s v%s' % (version.PRODUCT, version.VERSION))

        cfg = config.Config()

        db = database.Database()

        ebus = ebus_client.EbusClient()
        ebus.start()

        if cfg.daemonize():
            pass
        else:
            while True:
                time.sleep(1)

    finally:
        if ebus:
            ebus.stop()
            ebus.join()
            ebus.destroy()
            ebus = None
        if db:
            db = None
        logger.info('Done')


if __name__ == '__main__':
    main()
