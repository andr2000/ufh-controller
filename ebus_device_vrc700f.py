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
            param = 'Hc1ActualFlowTempDesired'
            res = self.read_0(param)
            self.float_or_die(res)
            temp_flow_desired = res

            param = 'z1ActualRoomTempDesired'
            res = self.read_0(param)
            self.float_or_die(res)
            temp_room_des = res

            param = 'z1RoomTemp'
            res = self.read_0(param)
            if res == 'inf':
                res = '-1'
                telegram.send_message('VRC700: Room temp: inf')
            self.float_or_die(res)
            temp_room = res

            param = 'z1DayTemp'
            res = self.read_0(param)
            self.float_or_die(res)
            temp_day = res

            param = 'z1NightTemp'
            res = self.read_0(param)
            self.float_or_die(res)
            temp_night = res

            param = 'DisplayedOutsideTemp'
            res = self.read_0(param)
            self.float_or_die(res)
            temp_outside = res

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
            telegram.send_message('BAI: Error: %s = %s' % (param, res))
            self.logger.error('%s: %s = %s' % (str(e), param, res))

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
