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
        power_max_hc = self.ebusd.read_parameter(
            self.message['power_max_hc'], self.scan_result.address)
        self.power_max_hc = float(power_max_hc[0])

    def process(self):
        flow_temp = self.ebusd.read_parameter(
            self.message['flow_temp'], self.scan_result.address)
        self.logger.info('Flow temperature is %.2f, sensor is %s' %
                         (float(flow_temp[0]), flow_temp[1]))
        return_temp = self.ebusd.read_parameter(
            self.message['return_temp'], self.scan_result.address)
        self.logger.info('Return temperature is %.2f sensor is %s' %
                         (float(return_temp[0]), return_temp[2]))
        flame = self.ebusd.read_parameter(
            self.message['flame'], self.scan_result.address)
        self.logger.info('Flame is %s' % flame[0])
        power_current_hc = self.ebusd.read_parameter(
            self.message['power_current_hc'], self.scan_result.address)
        power = float(power_current_hc[0])
        self.logger.info('Power HC, %.2f%% (%.1f kW)' %
                         (power, self.power_max_hc * power / 100.0))


    def __register_message(self, msg):
        # Check what message it is and assign it properly
        if msg.name == 'FlowTemp':
            self.message['flow_temp'] = msg
        elif msg.name == 'ReturnTemp':
            self.message['return_temp'] = msg
        elif msg.name == 'Flame':
            self.message['flame'] = msg
        elif msg.name == 'ModulationTempDesired':
            self.message['power_current_hc'] = msg
        elif msg.name == 'PartloadHcKW':
            self.message['power_max_hc'] = msg
