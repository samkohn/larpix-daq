'''
Formatter for LArPix data packets + medatadata to/from bytestreams.

'''
import json

from larpix.larpix import Packet, TimestampPacket

def toBytes(packets):
    return b'0.1/' + b''.join(p.bytes() + (
            b'\xAA' if isinstance(p, Packet) else b'\xBB')
        for p in packets)

def fromBytes(bytestream):
    version, slash, stream = bytestream.partition(b'/')
    if slash == b'':
        raise ValueError('No version found')
    split = [stream[n:n+8] for n in range(0, len(stream), 8)]
    packets = [Packet(x[:7]) if x[7]==b'\xAA'[0] else
            TimestampPacket(code=x[:7]) for x in split]
    return packets

def to_unicode_coding(packets):
    '''
    Return an encoding of the packet bytes as a Unicode string.

    '''
    return json.dumps([p.export() for p in packets])

def from_unicode_coding(unicode_stream):
    '''
    Convert the Unicode stream back into Packets.

    '''
    raise NotImplementedError()

def toDict(packets):
    return [p.export() for p in packets]

def fromDict(jsonlist):
    type_map = {
            'data': 0,
            'test': 1,
            'config write': 2,
            'config read': 3,
            }
    packets = []
    for item in jsonlist:
        p = Packet()
        p.packet_type = item['type']
        p.chipid = item['chipid']
        p.parity = item['parity']
        if item['type'] == 'data':
            p.channel = item['channel']
            p.timestamp = item['timestamp']
            p.dataword = item['adc_counts']
            p.fifo_half_flag = item['fifo_half']
            p.fifo_full_flag = item['fifo_full']
        elif item['type'] == 'test':
            p.counter = item['counter']
        elif (item['type'] == 'config write'
                or item['type'] == 'config read'):
            p.register_address = item['register']
            p.register_data = item['value']
    return packets

