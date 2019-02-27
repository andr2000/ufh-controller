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
            columns='timestamp,FlowDes,RoomDes,Room,Day,Night,Out',
            formatters={
                'timestamp': '{:%Y-%m-%d %H:%M:%S}'.format,
                'FlowDes': '{:,.2f}'.format,
                'RoomDes': '{:,.2f}'.format,
                'Room': '{:,.2f}'.format,
                'Day': '{:,.2f}'.format,
                'Night': '{:,.2f}'.format,
                'Out': '{:,.2f}'.format
            },
            colwidth={
                'FlowDes': 6, 'RoomDes': 6, 'Room': 6,
                'Day': 6, 'Night': 6, 'Out': 6
            })

        self.temp_room_des = self.read_0('z1ActualRoomTempDesired')

    def process(self):
        super().process()

        try:
            temp_flow_desired = self.read_0('Hc1ActualFlowTempDesired')
            self.float_or_die(temp_flow_desired)

            temp_room_des = self.read_0('z1ActualRoomTempDesired')
            self.float_or_die(temp_room_des)

            temp_room = self.read_0('z1RoomTemp')
            if temp_room == 'inf':
                temp_room = '-1'
            self.float_or_die(temp_room)

            temp_day = self.read_0('z1DayTemp')
            self.float_or_die(temp_day)

            temp_night = self.read_0('z1NightTemp')
            self.float_or_die(temp_night)

            temp_outside = self.read_0('DisplayedOutsideTemp')
            self.float_or_die(temp_outside)

            self.tbl(datetime.datetime.now(), float(temp_flow_desired),
                     float(temp_room_des), float(temp_room),
                     float(temp_day), float(temp_night), float(temp_outside))

            # store to the database
            values = {
                'FlowTempDesired': temp_flow_desired,
                'RoomTempDesired': temp_room_des,
                'RoomTemp': temp_room,
                'DayTemp': temp_day,
                'NightTemp': temp_night,
                'OutTemp': temp_outside,
                'RecLvlHead': -1,
                'RecLvlOut': -1
            }
            database.store_vrc700f(values)

            telegram.send_message('FlowDes %s RoomDes %s Room %s '
                                  'Day %s Night %s Out %s' %
                                  (temp_flow_desired, temp_room_des,
                                   temp_room, temp_day, temp_night,
                                   temp_outside))
        except ValueError as e:
            self.logger.error(str(e))

    def poll(self):
        res = False
        try:
            # Trigger faster processing after desired room temp has changed
            temp = self.read_0('z1ActualRoomTempDesired')
            res = temp != self.temp_room_des
            self.temp_room_des = temp
        except ValueError as e:
            pass

        return res
