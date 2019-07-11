from larpix.logger import Logger
from larpixdaq.packetformat import toBytes

class DAQLogger(Logger):
    '''
    Logs larpix-control packets to the DAQ pipeline.

    '''
    def __init__(self, producer):
        super(DAQLogger, self).__init__(self)
        self.producer = producer

    def record(self, data, direction=Logger.WRITE):
        if self.is_enabled():
            to_produce = toBytes(data)
            self.producer.produce(to_produce)
        else:
            pass
