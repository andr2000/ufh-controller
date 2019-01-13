import logging


class DeviceBAI(object):
    ebusd = None

    def __init__(self, ebusd, scan_result):
        self.logger = logging.getLogger(__name__)

        self.logger.info(
            'Creating new BAI device: make %s SW %s HW %s product %s' %
            (scan_result.make, scan_result.sw, scan_result.hw,
             scan_result.prod))
        self.ebusd = ebusd
        self.scan_result = scan_result

        self.supported_messages = self.ebusd.get_supported_messages(
            circuit=scan_result.circuit)
        self.message = {}
        for msg in self.supported_messages:
            self.__register_message(msg)

        flow_temp = self.ebusd.read_parameter(
            self.message['flow_temp'], self.scan_result.address)
        self.logger.info('Flow temperature is %f' % float(flow_temp[0]))

    def __register_message(self, msg):
        # Check what message it is and assign it properly
        if msg.name == 'FlowTemp':
            self.message['flow_temp'] = msg
        elif msg.name == 'ReturnTemp':
            self.message['return_temp'] = msg
