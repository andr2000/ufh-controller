from enum import Enum


class EbusdDeviceId(Enum):
    bai = "BAI00"


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
    def __init__(self, cs_string):
        # cs_string is a comma separated circuit,type,name
        list = cs_string.split(',')
        if not list:
            raise ValueError('Wrong or empty parameter list')
        self.circuit = EbusdCircuit(list[0])
        self.type = EbusdType(list[1])
        self.name = list[2]


class EbusdScanResult(object):
    def __init__(self, scan_string):
        # 08;Vaillant;BAI00;0104;7803;21;18;23;0010021961;0001;005167;N4
        vals = scan_string.split(';')
        if not vals:
            raise ValueError('Cannot parse scan result: %s' % scan_string)
        self.address = vals[0]
        self.make = vals[1]
        self.id = EbusdDeviceId(vals[2])
        self.sw = vals[3]
        self.hw = vals[4]
        self.prod = vals[8]
