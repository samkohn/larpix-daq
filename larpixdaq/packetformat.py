'''
Formatter for LArPix data packets + medatadata to/from bytestreams.

'''
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
