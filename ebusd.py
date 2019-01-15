from enum import Enum
import logging
import socket
import threading
import time
from threading import Thread

import config
from ebusd_types import (EbusdType, EbusdMessage, EbusdScanResult)

EBUSD_SOCK_TIMEOUT = 5
EBUSD_RECONNECT_TIMEOUT = 5
EBUSD_IO_RETRY_COUNT = 3


class EbusdErr(Enum):
    RESULT_ERR_GENERIC_IO = 'ERR: generic I/O error'
    RESULT_ERR_DEVICE = 'ERR: generic device error'
    RESULT_ERR_SEND = 'ERR: send error'
    RESULT_ERR_ESC = 'ERR: invalid escape sequence'
    RESULT_ERR_TIMEOUT = 'ERR: read timeout'
    RESULT_ERR_NOTFOUND = 'ERR: element not found'
    RESULT_ERR_EOF = 'ERR: end of input reached'
    RESULT_ERR_INVALID_ARG = 'ERR: invalid argument'
    RESULT_ERR_INVALID_NUM = 'ERR: invalid numeric argument'
    RESULT_ERR_INVALID_ADDR = 'ERR: invalid address'
    RESULT_ERR_INVALID_POS = 'ERR: invalid position'
    RESULT_ERR_OUT_OF_RANGE = 'ERR: argument value out of valid range'
    RESULT_ERR_INVALID_PART = 'ERR: invalid part type'
    RESULT_ERR_MISSING_ARG = 'ERR: missing argument'
    RESULT_ERR_INVALID_LIST = 'ERR: invalid value list'
    RESULT_ERR_DUPLICATE = 'ERR: duplicate entry'
    RESULT_ERR_DUPLICATE_NAME = 'ERR: duplicate name'
    RESULT_ERR_BUS_LOST = 'ERR: arbitration lost'
    RESULT_ERR_CRC = 'ERR: CRC error'
    RESULT_ERR_ACK = 'ERR: ACK error'
    RESULT_ERR_NAK = 'ERR: NAK received'
    RESULT_ERR_NO_SIGNAL = 'ERR: no signal'
    RESULT_ERR_SYN = 'ERR: SYN received'
    RESULT_ERR_SYMBOL = 'ERR: wrong symbol received'
    RESULT_ERR_NOTAUTHORIZED = 'ERR: not authorized'

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

class Ebusd(Thread):
    def __del__(self):
        self.disconnect()

    def __init__(self):
        super(Ebusd, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock()
        self.sock = None
        self._stop_event = threading.Event()

    def __del__(self):
        self.disconnect()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def is_connected(self):
        with self.lock:
            return self.sock

    def connect(self):
        self.logger.info('Connecting to ebusd...')
        try:
            cfg = config.Config()
            with self.lock:
                if self.sock:
                    self.sock.close()
                    self.sock = None
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(EBUSD_SOCK_TIMEOUT)
                self.sock.connect(((cfg.ebusd_address(), cfg.ebusd_port())))
        except socket.error:
            self.sock = None
            raise OSError('Not connected yet')
        self.logger.info('Connected')

    def disconnect(self):
        with self.lock:
            if self.sock:
                self.logger.info('Disconnecting from ebusd...')
                self.sock.close()
                self.logger.info('Disconnected')
            self.sock = None

    def run(self):
        # This is a reconnect thread.
        while not self.stopped():
            if self.sock:
                time.sleep(EBUSD_RECONNECT_TIMEOUT)
            else:
                try:
                    self.connect()
                except OSError:
                    time.sleep(EBUSD_RECONNECT_TIMEOUT)
                    pass

    def scan_devices(self):
        result = []
        reply = self.__scan(result=True)
        if reply:
            for line in reply.split('\n'):
                self.logger.debug('scanned %s' % line)
                try:
                    result.append(EbusdScanResult(line))
                except Exception as e:
                    self.logger.error('Skipping scan result %s: %s' %
                                      (line, str(e)))
        return result

    def __scan(self, result=True, full=False, address=''):
        cmd = 'scan '
        if result:
            cmd += 'result'
        elif full:
            cmd += 'full'
        elif address:
            cmd += address
        else:
            raise ValueError('Invalid combination of parameters')
        with self.lock:
            reply = self.__read(cmd)
            return reply

    def get_supported_messages(self, circuit=None):
        self.logger.info('Querying supported messages...')
        result = []
        with self.lock:
            reply = self.__read('find -F type,name')
            if circuit:
                reply += ' -c ' + circuit
            if reply:
                for line in reply.split('\n'):
                    # Validate the message
                    try:
                        msg = EbusdMessage(line)
                        result.append(msg.name)
                    except ValueError:
                        self.logger.error('Unsupported ebusd parameter %s',
                                          line)
                        continue
        return result

    def read_parameter(self, name, dest_addr=None):
        result = None
        with self.lock:
            args = ''
            if dest_addr:
                args += '-d ' + dest_addr + ' '
            args += name
            result = self.__read('read -f ' + args)
        return result

    def __recvall(self):
        # All socket access is serialized with the lock, so we can assume
        # that we can to read all the data in the receive buffer
        result = b''
        while True:
            # Read as many bytes as we can
            chunk = self.sock.recv(4096)
            if not chunk:
                # Disconnected - reconnect
                self.sock = None
                raise OSError('Disconnected from ebusd')
            result += chunk
            # ebusd response ends with a single empty line.
            if chunk.endswith(b'\n\n'):
                break
        return result

    def __read(self, command):
        try:
            command += '\n'
            for i in range(EBUSD_IO_RETRY_COUNT):
                self.sock.sendall(command.encode())
                result = self.__recvall().decode('utf-8').strip()
                # FIXME: sometimes ebusd returns 'Element not found' error
                # even for known messages, so try harder
                if result != EbusdErr.RESULT_ERR_NOTFOUND.value:
                    break
            # Check if reply is an error message
            if EbusdErr.has_value(result):
                raise ValueError(result)
        except socket.error:
            # Disconnected - reconnect
            self.sock = None
            raise OSError('Disconnected from ebusd')
        return result
