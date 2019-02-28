'''
Formatter for LArPix data packets + medatadata to/from bytestreams.

'''
from larpix.larpix import Packet

def toBytes(packets):
    return b'\xAA'.join(p.bytes() for p in packets)

def fromBytes(bytestream):
    split = [bytestream[n:n+8] for n in range(0, len(bytestream), 8)]
    packets = [Packet(x[:7]) for x in split]
    return packets
