import database
import datetime
import logging

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
        self.logger.info('Initializing new boiler device')

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

        self.power_max_hc_kw = float(self.bai_read_0('PartloadHcKW'))

    def process(self):
        super().process()

        try:
            temp_flow, temp_flow_status = self.bai_read_0_status_at_idx(
                'FlowTemp', 1)
            temp_flow_des = self.bai_read_0('FlowTempDesired')
            temp_return, temp_return_status = self.bai_read_0_status_at_idx(
                'ReturnTemp', 2)

            flame = self.bai_read_0('Flame')

            power = self.bai_read_0('ModulationTempDesired')
            power_kw = self.power_max_hc_kw * float(power) / 100.0

            water_pressure = self.bai_read_0('WaterPressure')

            pump_power = self.bai_read_0('PumpPower')

            status01 = self.bai_read_raw('Status01')
            status02 = self.bai_read_raw('Status02')

            set_mode_r = self.bai_read_raw_experimental(self.SetModeR)

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
            database.store_boiler(values)
        except ValueError as e:
            self.logger.error(str(e))
