from moddaq import Core
import os

core = Core('tcp://*:5550', 'tcp://*:5551')
core.address_service.bind_base = 'tcp://*'
core.address_service.connect_base = 'tcp://localhost:'
filepath = os.path.join(os.path.dirname(__file__), 'architecture.cfg')
architecture = core.address_service.loadFile(filepath)
core.run()
