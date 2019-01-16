import database
import datetime
import logging

from table_logger import TableLogger

# type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
SetModeR = 'r,bai,SetModeR,Operation Mode,,,b511,0100,,,temp0,,,,flowtempdesired,,temp1,,,,hwctempdesired,,temp1,,,,hwcflowtempdesired,,temp0,,,,,,IGN:1,,,,disablehc,,BI0,,,,disablehwctapping,,BI1,,,,disablehwcload,,BI2,,,,,,IGN:1,,,,remoteControlHcPump,,BI0,,,,releaseBackup,,BI1,,,,releaseCooling,,BI2,,,,'


class DeviceBAI(object):
    ebusd = None

    def __init__(self, ebusd, scan_result):
        self.logger = logging.getLogger(__name__)

        self.tbl = TableLogger(
            columns='timestamp,FlowDes,Flow,Return,Flame,Power,PowKW,WaterPres,PumpPow,Status01,Status02,SetModeR',
            formatters={
                'timestamp': '{:%Y-%m-%d %H:%M:%S}'.format,
                'FlowDes': '{:,.2f}'.format,
                'Flow': '{:,.2f}'.format,
                'Return': '{:,.2f}'.format,
                'Flame': '{:3}'.format,
                'Power': '{:,.2f}'.format,
                'PowKW': '{:,.2f}'.format,
                'PumpPow': '{:,.2f}'.format,
                'WaterPres': '{:,.3f}'.format,
            },
            colwidth={
                'Flow': 6, 'FlowDes': 6, 'Return': 6, 'Flame': 5, 'Power': 5,
                'PowKW': 5, 'WaterPres': 9, 'PumpPow': 7, 'Status01': 25,
                'Status02': 20, 'SetModeR': 27
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
        self.power_max_hc_kw = float(self.bai_read_float_0('PartloadHcKW'))

    def bai_read_float_0(self, msg):
        res = self.ebusd.read_parameter(msg,
                                        self.scan_result.address).split(';')
        return res[0]

    def bai_read_float_0_status(self, msg, status_idx):
        res = self.ebusd.read_parameter(msg,
                                        self.scan_result.address).split(';')
        return res[0], res[status_idx]

    def bai_read_int_0(self, msg):
        res = self.ebusd.read_parameter(msg,
                                        self.scan_result.address).split(';')
        return res[0]

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
            temp_flow, temp_flow_status = self.bai_read_float_0_status(
                'FlowTemp', 1)
            temp_flow_des = self.bai_read_float_0('FlowTempDesired')
            temp_return, temp_return_status = self.bai_read_float_0_status(
                'ReturnTemp', 2)

            flame = self.bai_read_str('Flame')

            power = self.bai_read_float_0('ModulationTempDesired')
            power_kw = self.power_max_hc_kw * float(power) / 100.0

            water_pressure = self.bai_read_float_0('WaterPressure')

            pump_power = self.bai_read_int_0('PumpPower')

            status01 = self.bai_read_str('Status01')
            status02 = self.bai_read_str('Status02')

            set_mode_r = self.bai_read_experimental(SetModeR)

            self.tbl(datetime.datetime.now(), float(temp_flow_des),
                     float(temp_flow), float(temp_return), flame, float(power),
                     power_kw, float(water_pressure), float(pump_power),
                     status01, status02, set_mode_r)
        except ValueError as e:
            self.logger.error(str(e))

        # store to the database
        values = {}
        values['FlowTemp'] = temp_flow
        values['FlowTemp_sensor'] = temp_flow_status
        values['FlowTempDesired'] = temp_flow_des
        values['ReturnTemp'] = temp_return
        values['ReturnTemp_sensor'] = temp_return_status
        values['Flame'] = flame
        values['PowerPercent'] = power
        values['WaterPressure'] = water_pressure
        values['PumpPower'] = pump_power
        values['Status01'] = status01
        values['Status02'] = status02
        values['SetModeR'] = set_mode_r
        database.store_boiler(values)
