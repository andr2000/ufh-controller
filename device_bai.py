import ebusd
import logging

class DeviceBAI:
    def __init__(self, scan_result):
        self.logger = logging.getLogger(__name__)

        self.logger.info('Creating new BAI device: make %s SW %s HW %s product %s' %
                         (scan_result.make, scan_result.sw, scan_result.hw,
                          scan_result.prod))
        self.scan_result = scan_result

        self.supported_messages = ebusd.Ebusd().get_supported_messages(
            circuit=scan_result.circuit)
        self.message = []
        for msg in self.supported_messages:
            self.__register_message(msg)

        flow_temp = ebusd.Ebusd().read_parameter(
            self.message['flow_temp'], self.scan_result.address)
        self.logger.info('Flow temperature is %s' % flow_temp)

    def __register_message(self, msg):
        # Check what message it is and assign it properly
        if msg.name == 'FlowTemp':
            self.message['flow_temp'] = msg
        elif msg.name == 'ReturnTemp':
            self.message['return_temp'] = msg
