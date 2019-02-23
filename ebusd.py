from enum import Enum
import logging
import socket

logger = logging.getLogger(__name__)

import config
from ebusd_types import (EbusdMessage, EbusdScanResult)

EBUSD_SOCK_TIMEOUT = 5


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
        return any(value.startswith(item.value) for item in cls)


sock = None


def is_connected():
    return sock


def connect():
    global sock

    if sock:
        return

    address = config.options['ebusd_address']
    port = config.options['ebusd_port']
    logger.info('Connecting to ebusd at %s:%d...', address, port)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(EBUSD_SOCK_TIMEOUT)
        sock.connect(((address, port)))
    except OSError:
        sock = None
        raise
    logger.info('Connected to ebusd')


def disconnect():
    global sock

    if sock:
        logger.info('Disconnecting from ebusd...')
        sock.close()
        logger.info('Disconnected from ebusd')
    sock = None


def scan_devices():
    logger.info('Scanning devices...')
    result = []
    reply = __scan(result=True)
    if reply:
        # Check if reply is an error message.
        if EbusdErr.has_value(reply):
            return result
        for line in reply.split('\n'):
            if 'done' in line:
                return result
            logger.debug('Device %s' % line)
            try:
                result.append(EbusdScanResult(line))
            except ValueError as e:
                logger.error('Skipping scan result %s: %s' % (line, str(e)))
    logger.info('Found %d device(s)', len(result))
    return result


def __scan(result=True, full=False, address=''):
    cmd = 'scan '
    if result:
        cmd += 'result'
    elif full:
        cmd += 'full'
    elif address:
        cmd += address
    else:
        raise ValueError('Invalid combination of parameters')
    return __read(cmd)


def get_supported_messages(circuit=None):
    logger.info('Querying supported messages...')
    result = []
    reply = __read('find -F type,name')
    if circuit:
        reply += ' -c ' + circuit
    if reply:
        for line in reply.split('\n'):
            # Validate the message
            try:
                msg = EbusdMessage(line)
                result.append(msg.name)
            except ValueError:
                logger.error('Unsupported ebusd parameter %s', line)
                continue
    return result


def read_parameter(name, circuit=None, dest_addr=None):
    result = None
    args = ''
    if circuit:
        args += '-c ' + circuit + ' '
    if dest_addr:
        args += ' -d ' + dest_addr + ' '
    args += name
    result = __read('read -f ' + args)
    return result


def read_exp_parameter(descriptor, circuit, dest_addr):
    args = '-def \"' + descriptor + '\"'
    return read_parameter(args, circuit, dest_addr)


def __recvall():
    global sock

    # All socket access is serialized with the lock, so we can assume
    # that we can to read all the data in the receive buffer.
    result = b''
    while True:
        # Read as many bytes as we can
        chunk = sock.recv(4096)
        if not chunk:
            # Disconnected - reconnect
            sock = None
            raise OSError('Disconnected from ebusd')
        result += chunk
        # ebusd response ends with a single empty line.
        if chunk.endswith(b'\n\n'):
            break
    return result


def __read(command, retry=3):
    global sock

    try:
        command += '\n'
        for i in range(retry):
            sock.sendall(command.encode())
            result = __recvall().decode('utf-8').strip()
            # FIXME: sometimes ebusd returns 'Element not found' error
            # even for known messages, so try harder.
            if result != EbusdErr.RESULT_ERR_NOTFOUND.value:
                break
        # Check if reply is an error message.
        if EbusdErr.has_value(result):
            raise ValueError(result)
    except OSError:
        # Disconnected - reconnect
        sock = None
        raise OSError('Disconnected from ebusd')
    return result
