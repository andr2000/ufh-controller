import logging
# FIXME: there should be some more elegant way to setup the logger globally
logging.basicConfig(level=logging.DEBUG)

import time

import config
import ebus_client
import version


log = logging.getLogger(__name__)

def main():
    ebus = None

    try:
        log.info('This is %s v%s' % (version.PRODUCT, version.VERSION))

        ebus = ebus_client.EbusClient()
        ebus.start()

        if config.options['daemonize']:
            pass
        else:
            while True:
                time.sleep(1)
    finally:
        if ebus:
            try:
                ebus.stop()
                ebus.join()
            except RuntimeError:
                pass
            del ebus
        log.info('Done')


if __name__ == '__main__':
    main()
