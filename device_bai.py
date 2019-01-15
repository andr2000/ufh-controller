import datetime
import logging

from table_logger import TableLogger

class DeviceBAI(object):
    ebusd = None

    def __init__(self, ebusd, scan_result):
        self.logger = logging.getLogger(__name__)

        self.tbl = TableLogger(
                columns='timestamp,FlowDes,Flow,Return,Flame,Power,PowKW,WaterPres,PumpPow,Status01, Status02',
                formatters={
                    'timestamp': '{:%Y-%m-%d %H:%M:%S}'.format,
                    'FlowDes': '{:,.2f}'.format,
                    'Flow': '{:,.2f}'.format,
                    'Return': '{:,.2f}'.format,
                    'Flame': '{:3}'.format,
                    'Power': '{:,.2f}'.format,
                    'PowKW': '{:,.2f}'.format,
                    'WaterPres': '{:,.3f}'.format,
                    },
                colwidth={
                    'Flow':6, 'FlowDes':6, 'Return':6, 'Flame':5, 'Power':5,
                    'PowKW':5, 'WaterPres':9, 'PumpPow':7, 'Status01':25,
                    'Status02':20
                    })

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
        try:
            res = self.ebusd.read_parameter(
                    self.message['flow_temp'], self.scan_result.address)
            temp_flow = float(res[0])

            res = self.ebusd.read_parameter(
                    self.message['flow_temp_des'], self.scan_result.address)
            temp_flow_des = float(res[0])

            res = self.ebusd.read_parameter(
                    self.message['return_temp'], self.scan_result.address)
            temp_return = float(res[0])

            res = self.ebusd.read_parameter(
                    self.message['flame'], self.scan_result.address)
            flame = res[0]

            res = self.ebusd.read_parameter(
                    self.message['power_current_hc'], self.scan_result.address)
            power = float(res[0])
            power_kw = self.power_max_hc * power / 100.0

            res = self.ebusd.read_parameter(
                    self.message['water_pressure'], self.scan_result.address)
            water_pressure = float(res[0])

            res = self.ebusd.read_parameter(
                    self.message['pump_power'], self.scan_result.address)
            pump_power = int(res[0])

            res = self.ebusd.read_parameter(
                    self.message['status01'], self.scan_result.address)
            status01 = ';'.join(res)

            res = self.ebusd.read_parameter(
                    self.message['status02'], self.scan_result.address)
            status02 = ';'.join(res)

            self.tbl(datetime.datetime.now(), temp_flow_des,
                    temp_flow, temp_return, flame, power, power_kw,
                    water_pressure, pump_power, status01, status02)
        except ValueError as e:
            self.logger.error(str(e))

    def __register_message(self, msg):
        # Check what message it is and assign it properly
        if msg.name == 'FlowTemp':
            self.message['flow_temp'] = msg
        elif msg.name == 'FlowTempDesired':
            self.message['flow_temp_des'] = msg
        elif msg.name == 'ReturnTemp':
            self.message['return_temp'] = msg
        elif msg.name == 'Flame':
            self.message['flame'] = msg
        elif msg.name == 'ModulationTempDesired':
            self.message['power_current_hc'] = msg
        elif msg.name == 'PartloadHcKW':
            self.message['power_max_hc'] = msg
        elif msg.name == 'WaterPressure':
            self.message['water_pressure'] = msg
        elif msg.name == 'Status01':
            self.message['status01'] = msg
        elif msg.name == 'Status02':
            self.message['status02'] = msg
        elif msg.name == 'PumpPower':
            self.message['pump_power'] = msg

