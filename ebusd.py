import config
import logging
import threading
import socket
from ebusd_types import (EbusdCircuit, EbusdType,
                         EbusdParameter, EbusdScanResult)

class Ebusd(object):
    __instance = None
    lock = None
    sock = None
    scanned_devices = []

    def __new__(cls):
        if Ebusd.__instance is None:
            Ebusd.__instance = object.__new__(cls)
            Ebusd.__instance.logger = logging.getLogger(__name__)
            Ebusd.__instance.lock = threading.Lock()
            Ebusd.__instance.connect()
        return Ebusd.__instance

    def __del__(self):
        self.disconnect()

    def connect(self):
        self.logger.info('Connecting to ebusd...')
        try:
            cfg = config.Config()
            with self.lock:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(cfg.ebusd_timeout())
                self.sock.connect(((cfg.ebusd_address(), cfg.ebusd_port())))
        except socket.timeout:
            raise socket.timeout(socket.timeout())
        except socket.error:
            raise socket.error(socket.error)
        self.logger.info('Connected')

    def disconnect(self):
        self.logger.info('Disconnecting from ebusd...')
        with self.lock:
            if self.sock:
                self.sock.close()
            self.sock = None
        self.logger.info('Disconnected')

    def scan_devices(self):
        result = []
        reply = self.__scan(result=True)
        if reply:
            for line in reply.split('\n'):
                self.logger.debug('scanned %s' % line)
                try:
                    result.append(EbusdScanResult(line))
                except Exception as e:
                    self.logger.error('Skipping scan result %s: %s' % (line, str(e)))
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
                    try:
                        result.append(EbusdParameter(line))
                    except ValueError:
                        self.logger.error('Unsupported ebusd parameter %s', line)
        return result

    def read_parameter(self, msg, dest_addr=None):
        result = None
        if msg.type != EbusdType.read:
            self.logger.error('Parameter %s has wrong type %s' %
                              (msg.name, msg.type))
            return result
        with self.lock:
            args = ''
            if dest_addr:
                args += '-d ' + dest_addr + ' '
            args += msg.name
            result = self.__read('read -f ' + args)
        return result

    def __recvall(self):
        chunk_sz = 4096
        result = b''
        while True:
            chunk = self.sock.recv(chunk_sz)
            result += chunk
            if len(chunk) < chunk_sz:
                break
        return result

    def __read(self, command):
        result = None
        try:
            command += '\n'
            self.sock.sendall(command.encode())
            result = self.__recvall().decode('utf-8').strip()
        except socket.timeout:
            raise socket.timeout(socket.timeout)
        except socket.error:
            raise socket.error(socket.error)
        return result
