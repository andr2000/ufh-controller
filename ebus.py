import logging
import telegram
import threading
import time
from enum import Enum

import ebus_device_bai
import ebus_device_vrc700f
import ebusd
from ebusd_types import (EbusdDeviceId)


EBUS_RECONNECT_TO_SEC = 5
EBUS_POLL_TO_SEC = 15
EBUS_RUNNING_NORMAL_TO_SEC = 600
EBUS_RUNNING_FAST_TO_SEC = EBUS_POLL_TO_SEC
cur_running_to_sec = EBUS_RUNNING_NORMAL_TO_SEC
# This is used to limit print rate of "no signal" error
EBUS_LOGGER_NO_SIGNAL_TO_SEC = 5
EBUS_TELEGRAM_NO_SIGNAL_TO_SEC = 600

# This holds the number of devices found during the last scan.
# Some of the devices are detected late, so we need to re-scan
# periodically to catch those.
num_scanned_devices = 0

class EbusClientState(Enum):
    initializing = 'initializing'
    connecting = 'connecting'
    scanning = 'scanning'
    running = 'running'
    terminating = 'terminating'
    no_signal = 'no_signal'


class Ebus(threading.Thread):
    def __init__(self):
        super(Ebus, self).__init__()
        self.state = EbusClientState.initializing
        self.last_good_state = EbusClientState.no_signal
        self._stop_event = threading.Event()
        self.logger = logging.getLogger(__name__)
        self.print_no_signal = EBUS_LOGGER_NO_SIGNAL_TO_SEC
        self.print_no_signal_telegram = EBUS_TELEGRAM_NO_SIGNAL_TO_SEC

    def __del__(self):
        self.logger.info('Done')

    def stop(self):
        self.logger.info('Terminating now...')
        self.state = EbusClientState.terminating
        # This is used to track the state when device signal was lost
        self.last_good_state = EbusClientState.no_signal
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    @staticmethod
    def relax():
        time.sleep(1)

    def set_state(self, state):
        if self.state.value == state.value:
            return
        self.logger.debug('Going from state <%s> to <%s>' %
                          (self.state.value, state.value))
        if state.value == EbusClientState.no_signal.value:
            self.last_good_state = self.state
        self.state = state

    def check_signal(self):
        try:
            ebusd.check_signal()
        except ValueError as e:
            self.set_state(EbusClientState.no_signal)
            if str(e) == ebusd.EbusdErr.RESULT_ERR_NO_SIGNAL.value:
                self.print_no_signal += 1
                if self.print_no_signal > EBUS_LOGGER_NO_SIGNAL_TO_SEC:
                    self.print_no_signal = 0
                    self.logger.error(str(e))
                self.print_no_signal_telegram += 1
                if self.print_no_signal_telegram > EBUS_TELEGRAM_NO_SIGNAL_TO_SEC:
                    self.print_no_signal_telegram = 0
                    telegram.send_message(str(e))
            raise e


    def state_initializing(self):
        self.devices = []
        ebusd.disconnect()
        self.set_state(EbusClientState.connecting)
        return False

    def state_connecting(self):
        if ebusd.is_connected():
            self.set_state(EbusClientState.scanning)
        else:
            try:
                ebusd.connect()
            except OSError as e:
                self.logger.debug(str(e))

            if not ebusd.is_connected():
                return True
            self.set_state(EbusClientState.scanning)
        return False

    def state_scanning(self):
        global num_scanned_devices

        self.check_signal()

        scan_results = ebusd.scan_devices()
        if not scan_results:
            self.logger.warning('No devices found, continue scanning')
            return True

        for scan_result in scan_results:
            if scan_result.id == EbusdDeviceId.bai:
                self.devices.append(ebus_device_bai.EbusDeviceBAI(scan_result))
            elif scan_result.id == EbusdDeviceId.b7v:
                self.devices.append(ebus_device_vrc700f.EbusDeviceVRC700F(
                    scan_result))
            else:
                self.logger.error('Unsupported device %s' % scan_result.id)
        if self.devices:
            self.set_state(EbusClientState.running)
        else:
            self.logger.warning('No supported devices found, continue scanning')
            return True
        num_scanned_devices = len(scan_results)
        return False

    def state_running(self):
        self.check_signal()
        for dev in self.devices:
            dev.process()
        return True

    def state_no_signal(self):
        self.check_signal()
        # No exception means we can get back into the previous state
        self.set_state(self.last_good_state)
        self.print_no_signal = EBUS_LOGGER_NO_SIGNAL_TO_SEC
        self.print_no_signal_telegram = EBUS_TELEGRAM_NO_SIGNAL_TO_SEC
        return True

    def state_running_do_poll(self):
        fast_poll = False
        self.check_signal()
        for dev in self.devices:
            if dev.poll():
                fast_poll = True
        return fast_poll

    def run(self):
        global cur_running_to_sec
        seconds_till_run = 0
        seconds_till_poll = 0
        first_connect = True
        first_run = True
        while not self.stopped():
            try:
                if self.state == EbusClientState.initializing:
                    relax = self.state_initializing()
                elif self.state == EbusClientState.connecting:
                    if not first_connect:
                        seconds_till_run += 1
                        if seconds_till_run > EBUS_RECONNECT_TO_SEC:
                            seconds_till_run = 0
                            relax = self.state_connecting()
                        else:
                            relax = True
                    else:
                        first_connect = False
                        relax = self.state_connecting()
                elif self.state == EbusClientState.scanning:
                    relax = self.state_scanning()
                elif self.state == EbusClientState.no_signal:
                    relax = self.state_no_signal()
                    # Run now if we were in running state, do not wait for
                    # timeout
                    first_run = True
                elif self.state == EbusClientState.running:
                    if not first_run:
                        seconds_till_run += 1
                        if seconds_till_run > cur_running_to_sec:
                            seconds_till_run = 0
                            relax = self.state_running()
                        else:
                            relax = True
                    else:
                        first_run = False
                        seconds_till_run = 0
                        relax = self.state_running()

                    seconds_till_poll += 1
                    if seconds_till_poll > EBUS_POLL_TO_SEC:
                        if self.state_running_do_poll():
                            cur_running_to_sec = EBUS_RUNNING_FAST_TO_SEC
                        else:
                            cur_running_to_sec = EBUS_RUNNING_NORMAL_TO_SEC

                        # Check if new devices are here
                        scan_results = ebusd.scan_devices(silent=True)
                        if scan_results and (num_scanned_devices !=
                                             len(scan_results)):
                            # Device number has changed - re-scan
                            self.set_state(EbusClientState.initializing)
                            telegram.send_message(
                                'Number of eBus devices changed from %d to %d.'
                                ' Re-initializing now...' %
                                (num_scanned_devices, len(scan_results)))
                            # Force process the devices
                            seconds_till_run = cur_running_to_sec

                        seconds_till_poll = 0
                else:
                    self.logger.debug('Idle')
                    relax = True
            except ValueError:
                relax = True
                pass
            except OSError as e:
                self.logger.error("OS error: %s", str(e))
                self.set_state(EbusClientState.initializing)

            if relax:
                self.relax()

        self.devices = []
        ebusd.disconnect()
