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
            self.logger.debug('Supported message: %s' % msg)
        self.power_max_hc_kw = self.bai_read_float_0('PartloadHcKW')

    def bai_read_float_0(self, msg):
        res = self.ebusd.read_parameter(msg,
                                        self.scan_result.address).split(';')
        return float(res[0])

    def bai_read_int_0(self, msg):
        res = self.ebusd.read_parameter(msg,
                                        self.scan_result.address).split(';')
        return int(res[0])

    def bai_read_str(self, msg):
        res = self.ebusd.read_parameter(msg,
                                        self.scan_result.address)
        return res

    def bai_read_experimental(self, msg):
        res = self.ebusd.read_exp_parameter(msg,
                                            self.scan_result.address)
        return res

    def process(self):
        try:
            temp_flow = self.bai_read_float_0('FlowTemp')
            temp_flow_des = self.bai_read_float_0('FlowTempDesired')
            temp_return = self.bai_read_float_0('ReturnTemp')

            flame = self.bai_read_str('Flame')

            power = self.bai_read_float_0('ModulationTempDesired')
            power_kw = self.power_max_hc_kw * power / 100.0

            water_pressure = self.bai_read_float_0('WaterPressure')

            pump_power = self.bai_read_int_0('PumpPower')

            status01 = self.bai_read_str('Status01')
            status02 = self.bai_read_str('Status02')

            self.tbl(datetime.datetime.now(), temp_flow_des,
                     temp_flow, temp_return, flame, power, power_kw,
                     water_pressure, pump_power, status01, status02)
        except ValueError as e:
            self.logger.error(str(e))
