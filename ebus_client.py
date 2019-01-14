import logging
import socket
import threading
import time
from enum import Enum

import device_bai
import ebusd
from ebusd_types import (EbusdDeviceId)


class EbusClientState(Enum):
    unknown = 'unknown'
    initializing = 'initializing'
    connecting = 'connecting'
    scanning = 'scanning'
    running = 'running'
    terminating = 'terminating'


class EbusClient(threading.Thread):
    __instance = None
    ebusd = None
    state = EbusClientState.unknown
    devices = []

    def __new__(cls):
        if EbusClient.__instance is None:
            EbusClient.__instance = object.__new__(cls)
            EbusClient.__instance.logger = logging.getLogger(__name__)
            EbusClient.__instance.lock = threading.Lock()
            EbusClient.__instance.state = EbusClientState.initializing
        return EbusClient.__instance

    def __del__(self):
        self.logger.info('Done')

    @classmethod
    def destroy(cls):
        del cls.__instance

    def __init__(self):
        super(EbusClient, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self.logger.info('Terminating now...')
        self.state = EbusClientState.terminating
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def stop_ebusd(self):
        if self.ebusd:
            self.ebusd.stop()
            self.ebusd.join()
            self.ebusd = None

    @staticmethod
    def relax():
        time.sleep(1)

    def set_state(self, state):
        self.logger.debug('Going from state <%s> to <%s>' %
                          (self.state.value, state.value))
        self.state = state

    def state_initializing(self):
        self.stop_ebusd()
        self.ebusd = ebusd.Ebusd()
        self.set_state(EbusClientState.connecting)
        self.ebusd.start()

    def state_connecting(self):
        if self.ebusd.is_connected():
            self.set_state(EbusClientState.scanning)
        else:
            self.relax()

    def state_scanning(self):
        try:
            scan_results = self.ebusd.scan_devices()
        except socket.error as e:
            self.logger.error('Scan error: %s', e.strerror(e))
            self.set_state(EbusClientState.initializing)
        finally:
            if not scan_results:
                self.logger.warning('No devices found, continue scanning')
                self.relax()
                return

        self.logger.info('Found %s device(s)' % len(scan_results))
        for dev in scan_results:
            if dev.id == EbusdDeviceId.bai:
                self.devices.append(device_bai.DeviceBAI(self.ebusd, dev))
            else:
                self.logger.error('Unsupported device %s' % dev.id)
        if self.devices:
            self.set_state(EbusClientState.running)
        else:
            self.logger.warning('No supported devices found, continue scanning')
            self.relax()

    def state_running(self):
        for dev in self.devices:
            dev.process()
        time.sleep(10)

    def run(self):
        while not self.stopped():
            if self.state == EbusClientState.initializing:
                self.state_initializing()
            elif self.state == EbusClientState.connecting:
                self.state_connecting()
            elif self.state == EbusClientState.scanning:
                self.state_scanning()
            elif self.state == EbusClientState.running:
                self.state_running()
            else:
                self.logger.debug('Idle')
                self.relax()

        self.stop_ebusd()
