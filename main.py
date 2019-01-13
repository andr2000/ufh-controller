import logging
import time

import config
import ebus_client
import version


def main():
    global ebus_client

    try:
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info('This is %s v%s' % (version.PRODUCT, version.VERSION))

        cfg = config.Config()

        ebus_client = ebus_client.EbusClient()
        ebus_client.start()

        if cfg.daemonize():
            pass
        else:
            while True:
                time.sleep(1)

    finally:
        if ebus_client:
            ebus_client.stop()
            ebus_client.join()
            ebus_client.destroy()
            ebus_client = None
        logger.info('Done')


if __name__ == '__main__':
    main()
