import ebusd
import logging

class DeviceBAI:
    def __init__(self, scan_result):
        self.logger = logging.getLogger(__name__)

        self.logger.info('Creating new BAI device: make %s, SW %s HW %s product %s' %
                         (scan_result.make, scan_result.sw, scan_result.hw,
                          scan_result.prod))
        supported_messages = ebusd.Ebusd().get_supported_messages(
            circuit=scan_result.circuit)
        for msg in supported_messages:
            self.logger.info('Message %s:%s' %(msg.type, msg.name))
