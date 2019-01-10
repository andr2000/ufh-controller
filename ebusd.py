import config
import logging
import threading
import socket


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
            logging.debug(result)
        except socket.timeout:
            raise socket.timeout(socket.timeout)
        except socket.error:
            raise socket.error(socket.error)
        return result
