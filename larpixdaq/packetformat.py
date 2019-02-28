'''
Formatter for LArPix data packets + medatadata to/from bytestreams.

'''
import base64

from larpix.larpix import Packet

def toBytes(packets):
    return b'0.1/' + b'\xAA'.join(p.bytes() for p in packets)

def fromBytes(bytestream):
    version, slash, stream = bytestream.partition(b'/')
    if slash == b'':
        raise ValueError('No version found')
    split = [stream[n:n+8] for n in range(0, len(stream), 8)]
    packets = [Packet(x[:7]) for x in split]
    return packets

def to_unicode_coding(packets):
    '''
    Return an encoding of the packet bytes as a Unicode string.

    '''
    packet_bytes = toBytes(packets)
    b64bytes = base64.b64encode(packet_bytes)
    return b64bytes.decode()

def from_unicode_coding(unicode_stream):
    '''
    Convert the Unicode stream back into Packets.

    '''
    b64bytes = unicode_stream.encode()
    packet_bytes = base64.b64decode(b64bytes)
    return fromBytes(packet_bytes)

