import ebusd
import logging
from ebusd_types import (EbusdDeviceId, EbusdScanResult)

class DeviceBAI:
    def __init__(self, scan_result):
        self.logger = logging.getLogger(__name__)

        self.logger.info('Creating new BAI device: make %s, SW %s HW %s product %s' %
                         (scan_result.make, scan_result.sw, scan_result.hw,
                          scan_result.prod))
