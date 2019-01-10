import config
from enum import Enum
import logging
import threading
import socket


class EbusdCircuit(Enum):
    unknown = 'unknown'
    bai = 'bai'
    broadcast = 'broadcast'
    general = 'general'
    memory = 'memory'
    scan = 'scan'


class EbusdType(Enum):
    unknown = 'unknown'
    read = 'r'
    write = 'w'
    update = 'u'
    update_on_write = 'uw'


class EbusdParameter(object):
    circuit = None
    type = None
    name = None

    def __init__(self, cs_string):
        '''cs_string is a comma separated circuit,type,name'''
        list = cs_string.split(',')
        if not list:
            raise SyntaxError('Wrong or empty parameter list')
        self.circuit = EbusdCircuit(list[0])
        self.type = EbusdType(list[1])
        self.name = list[2]

    def GetCircuit(self):
        return self.circuit.value

    def GetType(self):
        return self.type.value

    def GetName(self):
        return self.name


class Ebusd(object):
    __instance = None
    lock = None
    sock = None

    def __new__(cls):
        if Ebusd.__instance is None:
            Ebusd.__instance = object.__new__(cls)
            Ebusd.__instance.lock = threading.Lock()
            Ebusd.__instance.connect()
            Ebusd.__instance.find()
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

    def find(self):
        logging.info('Querying the supported messages...')
        result = None
        with self.lock:
            result = self.__read('find -F circuit,type,name')
            if result:
                for line in result.split('\n'):
                    try:
                        param = EbusdParameter(line)
                        logging.debug('Parameter circuit: %s type: %s name: %s' %
                                  (param.GetCircuit(), param.GetType(),
                                   param.GetName()))
                    except ValueError:
                        logging.error('Unsupported ebusd parameter %s', line)

        logging.debug(result)

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
