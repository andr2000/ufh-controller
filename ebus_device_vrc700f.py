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

    def process(self):
        super().process()

        try:
            pass
        except ValueError as e:
            self.logger.error(str(e))
