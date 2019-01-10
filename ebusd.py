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
            Ebusd.__instance.lock = threading.Lock()
            Ebusd.__instance.connect()
        return Ebusd.__instance

    def __del__(self):
        self.disconnect()

    def connect(self):
        logging.info('Connecting to ebusd...')
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
        logging.info('Connected')

    def disconnect(self):
        logging.info('Disconnecting from ebusd...')
        with self.lock:
            if self.sock:
                self.sock.close()
            self.sock = None
        logging.info('Disconnected')

    def scan_devices(self):
        result = []
        reply = self.__scan(result=True)
        if reply:
            for line in reply.split('\n'):
                logging.debug('scanned %s' % line)
                try:
                    result.append(EbusdScanResult(line))
                except Exception as e:
                    logging.error('Skipping scan result %s: %s' % (line, str(e)))
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

    def find(self):
        logging.info('Querying the supported messages...')
        with self.lock:
            reply = self.__read('find -F circuit,type,name')
            if reply:
                for line in reply.split('\n'):
                    try:
                        param = EbusdParameter(line)
                        logging.debug('Parameter circuit: %s type: %s name: %s' %
                                  (param.circuit.value, param.type.value,
                                   param.name))
                    except ValueError:
                        logging.error('Unsupported ebusd parameter %s', line)

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
