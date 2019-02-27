import database
import datetime
import logging
import telegram

from ebus_device import EbusDevice
from table_logger import TableLogger


class EbusDeviceBAI(EbusDevice):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    SetModeR = 'r,bai,SetModeR,Operation Mode,,,b511,0100,,,temp0,,,,'\
               'flowtempdesired,,temp1,,,,hwctempdesired,,temp1,,,,'\
               'hwcflowtempdesired,,temp0,,,,,,IGN:1,,,,disablehc,,BI0,,,,'\
               'disablehwctapping,,BI1,,,,disablehwcload,,BI2,,,,,,IGN:1,,,,'\
               'remoteControlHcPump,,BI0,,,,releaseBackup,,BI1,,,,'\
               'releaseCooling,,BI2,,,,'

    def __init__(self, scan_result):
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initializing new burner device')

        super().__init__(scan_result)

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

        self.power_max_hc_kw = float(self.read_0('PartloadHcKW'))
        self.flame = self.read_0('Flame')

    def process(self):
        super().process()

        try:
            param = 'FlowTemp'
            res, temp_flow_status = self.read_0_status_at_idx(param, 1)
            self.float_or_die(res)
            temp_flow = res

            param = 'FlowTempDesired'
            res = self.read_0(param)
            self.float_or_die(res)
            temp_flow_des = res

            param = 'ReturnTemp'
            res, temp_return_status = self.read_0_status_at_idx(param, 2)
            self.float_or_die(res)
            temp_return = res

            param = 'Flame'
            res = self.read_0(param)
            flame = res

            param = 'ModulationTempDesired'
            res = self.read_0(param)
            self.float_or_die(res)
            power = res
            power_kw = self.power_max_hc_kw * float(power) / 100.0

            param = 'WaterPressure'
            res = self.read_0(param)
            self.float_or_die(res)
            water_pressure = res

            param = 'PumpPower'
            res = self.read_0(param)
            self.float_or_die(res)
            pump_power = res

            param = 'Status01'
            res = self.read_raw(param)
            status01 = res

            param = 'Status02'
            res = self.read_raw(param)
            status02 = res

            param = 'SetModeR'
            res = self.read_raw_experimental(self.SetModeR)
            set_mode_r = res

            self.tbl(datetime.datetime.now(), float(temp_flow_des),
                     float(temp_flow), float(temp_return), flame, float(power),
                     power_kw, float(water_pressure), float(pump_power),
                     status01, status02, set_mode_r)

            # store to the database
            values = {
                'FlowTemp': temp_flow,
                'FlowTemp_sensor': temp_flow_status,
                'FlowTempDesired': temp_flow_des,
                'ReturnTemp': temp_return,
                'ReturnTemp_sensor': temp_return_status,
                'Flame': flame,
                'PowerPercent': power,
                'WaterPressure': water_pressure,
                'PumpPower': pump_power,
                'Status01': status01,
                'Status02': status02,
                'SetModeR': set_mode_r}
            database.store_burner(values)

            telegram.send_message('Flow %s Return %s Power, kW %.3f Flame %s PumpPower %s' %
                                  (temp_flow, temp_return, power_kw, flame, pump_power))
        except ValueError as e:
            telegram.send_message('BAI: Error: %s = %s' % (param, res))
            self.logger.error('%s: %s = %s' % (str(e), param, res))

    def poll(self):
        try:
            # Trigger faster processing after Flame state has changed
            flame = self.read_0('Flame')
            res = flame != self.flame
            self.flame = flame
        except ValueError as e:
            pass

        return res
