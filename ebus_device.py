import logging

import ebusd
import telegram


class EbusDevice():
    def __init__(self, scan_result):
        self.logger = logging.getLogger(__name__)

        self.logger.info(
            'Creating new %s device: make %s SW %s HW %s product %s' %
            (scan_result.circuit, scan_result.make, scan_result.sw,
             scan_result.hw, scan_result.prod))
        self.scan_result = scan_result
        telegram.send_message_now('%s device: make %s SW %s HW %s product %s' %
                                  (scan_result.circuit, scan_result.make,
                                   scan_result.sw, scan_result.hw,
                                   scan_result.prod))

    def __del__(self):
        self.logger.info('Done')

    @staticmethod
    def float_or_die(val):
        float(val)

    @staticmethod
    def int_or_die(val):
        int(val)

    def read_0(self, msg):
        res = ebusd.read_parameter(msg,
                                   self.scan_result.circuit,
                                   self.scan_result.address).split(
            ';')
        return res[0]

    def read_0_status_at_idx(self, msg, status_idx):
        res = ebusd.read_parameter(msg, self.scan_result.circuit,
                                   self.scan_result.address).split(';')
        if status_idx >= len(res):
            raise ValueError()
        return res[0], res[status_idx]


    def read_raw(self, msg):
        res = ebusd.read_parameter(msg, self.scan_result.circuit,
                                   self.scan_result.address)
        return res

    def read_raw_experimental(self, msg):
        # Circuit is provided in the command itself
        res = ebusd.read_exp_parameter(msg, '', self.scan_result.address)
        return res

    def process(self):
        pass
