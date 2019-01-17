import logging

import ebusd


class EbusDevice():
    def __init__(self, scan_result):
        self.logger = logging.getLogger(__name__)

        self.logger.info(
            'Creating new BAI device: make %s SW %s HW %s product %s' %
            (scan_result.make, scan_result.sw, scan_result.hw,
             scan_result.prod))
        self.scan_result = scan_result

    def __del__(self):
        self.logger.info('Done')

    @staticmethod
    def bai_float_or_die(self, val):
        float(val)

    @staticmethod
    def bai_int_or_die(self, val):
        int(val)

    def bai_read_0(self, msg):
        res = ebusd.read_parameter(msg, self.scan_result.address).split(';')
        return res[0]

    def bai_read_0_status_at_idx(self, msg, status_idx):
        res = ebusd.read_parameter(msg, self.scan_result.address).split(';')
        if status_idx >= len(res):
            raise ValueError()
        return res[0], res[status_idx]


    def bai_read_raw(self, msg):
        res = ebusd.read_parameter(msg, self.scan_result.address)
        return res

    def bai_read_raw_experimental(self, msg):
        res = ebusd.read_exp_parameter(msg, self.scan_result.address)
        return res

    def process(self):
        pass
