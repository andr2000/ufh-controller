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
EBUS_POLL_TO_SEC = 600


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


class Ebus(threading.Thread):
    def __init__(self):
        super(Ebus, self).__init__()
        self.state = EbusClientState.initializing
        self._stop_event = threading.Event()
        self.logger = logging.getLogger(__name__)

    def __del__(self):
        self.logger.info('Done')

    def stop(self):
        self.logger.info('Terminating now...')
        self.state = EbusClientState.terminating
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    @staticmethod
    def relax():
        time.sleep(1)

    def set_state(self, state):
        self.logger.debug('Going from state <%s> to <%s>' %
                          (self.state.value, state.value))
        self.state = state

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
        # Check if new devices are here
        scan_results = ebusd.scan_devices(silent=True)
        if scan_results and (num_scanned_devices != len(scan_results)):
            # Device number has changed - re-scan
            self.set_state(EbusClientState.initializing)
            telegram.send_message('Number of eBus devices changed from %d to %d.'
                                  ' Re-initializing now...' %
                                  (num_scanned_devices, len(scan_results)))


        for dev in self.devices:
            dev.process()
        return True

    def run(self):
        seconds_till_run = 0
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
                elif self.state == EbusClientState.running:
                    if not first_run:
                        seconds_till_run += 1
                        if seconds_till_run > EBUS_POLL_TO_SEC:
                            seconds_till_run = 0
                            relax = self.state_running()
                        else:
                            relax = True
                    else:
                        first_run = False
                        seconds_till_run = 0
                        relax = self.state_running()
                else:
                    self.logger.debug('Idle')
                    relax = True
            except (ValueError):
                pass
            except OSError as e:
                self.logger.error("OS error: %s", str(e))
                self.set_state(EbusClientState.initializing)

            if relax:
                self.relax()

        self.devices = []
        ebusd.disconnect()
