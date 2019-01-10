import config
import device_bai
import ebusd
import logging
import version
from ebusd_types import (EbusdDeviceId, EbusdScanResult)


def main():
    try:
        devices = []

        logging.basicConfig(level=logging.DEBUG)
        logging.info('This is %s v%s' % (version.PRODUCT, version.VERSION))
        scan_results = ebusd.Ebusd().scan_devices()
        if not scan_results:
            raise SystemError('No devices found')
        logging.info('Found %s device(s)' % len(scan_results))
        for dev in scan_results:
            if dev.id == EbusdDeviceId.bai:
                devices.append(device_bai.DeviceBAI(dev))
            else:
                logging.error('Unsupported device %s' % dev.id)
    finally:
        logging.info('Done')


if __name__ == '__main__':
    main()
