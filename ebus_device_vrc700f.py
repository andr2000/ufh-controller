import database
import datetime
import logging
import telegram

from ebus_device import EbusDevice
from table_logger import TableLogger


class EbusDeviceVRC700F(EbusDevice):
    def __init__(self, scan_result):
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initializing new temperature regulator device')

        super().__init__(scan_result)

        self.tbl = TableLogger(
            columns='timestamp,FlowDes,Flow,RoomDes,RoomTemp,DayTemp,NightTemp,'
                    'OutTemp',
            formatters={
                'timestamp': '{:%Y-%m-%d %H:%M:%S}'.format,
                'FlowDes': '{:,.2f}'.format,
                'Flow': '{:,.2f}'.format,
                'RoomDes': '{:,.2f}'.format,
                'RoomTemp': '{:,.2f}'.format,
                'DayTemp': '{:,.2f}'.format,
                'NightTemp': '{:,.2f}'.format,
                'OutTemp': '{:,.2f}'.format
            },
            colwidth={
                'FlowDes': 6, 'Flow': 6, 'RoomDes': 6, 'RoomTemp': 6,
                'DayTemp': 6, 'NightTemp': 6, 'OutTemp': 6
            })

    def process(self):
        super().process()

        try:
            temp_flow_desired = self.read_0('Hc1ActualFlowTempDesired')
            self.float_or_die(temp_flow_desired)

            temp_flow = self.read_0('Hc1FlowTemp')
            self.float_or_die(temp_flow)

            temp_room_des = self.read_0('z1ActualRoomTempDesired')
            self.float_or_die(temp_room_des)

            temp_room = self.read_0('z1RoomTemp')
            self.float_or_die(temp_room)

            temp_day = self.read_0('z1DayTemp')
            self.float_or_die(temp_day)

            temp_night = self.read_0('z1NightTemp')
            self.float_or_die(temp_night)

            temp_outside = self.read_0('DisplayedOutsideTemp')
            self.float_or_die(temp_outside)

            self.tbl(datetime.datetime.now(), float(temp_flow_desired),
                     float(temp_flow), float(temp_room_des), float(temp_room),
                     float(temp_day), float(temp_night), float(temp_outside))

            telegram.send_message('FlowTDes %s FlowT %s RoomTDes %s RoomT %s '
                                  'DayT %s NightT %s OutT %s' %
                                  (temp_flow_desired, temp_flow, temp_room_des,
                                   temp_room, temp_day, temp_night,
                                   temp_outside))
        except ValueError as e:
            self.logger.error(str(e))
