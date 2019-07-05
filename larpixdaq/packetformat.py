'''
Formatter for LArPix data packets + medatadata to/from bytestreams.

'''
import json
import struct

from larpix.larpix import Packet, TimestampPacket

def get_packet(packet_bytes):
    byte_marker = packet_bytes[0]
    if byte_marker == 0:
        p = Packet(packet_bytes[1:8])
        p.chip_key = '%d-%d-%d' % (
                packet_bytes[8],
                packet_bytes[9],
                p.chipid)
        return p
    elif byte_marker == 1:
        return TimestampPacket(code=packet_bytes[1:8])

def format_packet(packet):
    if isinstance(packet, Packet):
        result = b'\x00' + packet.bytes()
        if packet.chip_key is None:
            io_group = 0
            io_channel = 0
        else:
            io_group = packet.chip_key.io_group
            io_channel = packet.chip_key.io_channel
        result += struct.pack('BB', io_group, io_channel)
        return result
    elif isinstance(packet, TimestampPacket):
        return b'\x01' + packet.bytes() + b'\x00\x00'


def toBytes(packets):
    '''
    Format the packets into a single bytestream.

    Format:

    - First 2 bytes, interpreted as integer values, are the version (major
    is byte 0, minor is byte 1).
    - Next is the ``b'/'`` character (`` == b'\x2F'``)
    - Then each packet takes 10 bytes:
        - First the packet-type indicator (``b'\x00'`` for data packets,
          ``b'\x01'`` for timestamps, etc.)
        - Then the packet data itself:
            - For data packets, 7 UART bytes from ``Packet.bytes()``
              (bytes 1-7), then the chip key data in 2 bytes: byte 8 is the
              IO group, and byte 9 is the IO channel. (The chip ID is
              contained in the UART bytes.)
            - For the timestamp packets, 7 timestamp bytes followed by
              2 unused bytes.

    '''

    return b'\x00\x01/' + b''.join(format_packet(p) for p in packets)

def fromBytes(bytestream):
    version, slash, stream = bytestream.partition(b'/')
    if slash == b'':
        raise ValueError('No version found')
    split = [stream[n:n+10] for n in range(0, len(stream), 10)]
    packets = [get_packet(x) for x in split]
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

