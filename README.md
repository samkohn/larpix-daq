# larpix-moddaq

LArPix DAQ is the data acquisition system for LArPix. It handles the
data flow between the "data boards" and offline storage and includes
data monitoring and operator control functionality.

LArPix DAQ consists of a set of scripts which are responsible for
individual parts of the DAQ system's functionality, as well as an
operator interface API which can be run in an interactive python session
or used as a basis for a more sophisticated interactive program. The
scripts can be run from the same or from different computers, as long as
the IP addresses of the various computers are known.

## Core

- Location: ``larpixdaq/core.py``

- Example invocation: ``python core.py --address tcp://127.0.0.1``

### Help text

```
usage: core.py [-h] [--address ADDRESS] [--log-address LOG_ADDRESS]

optional arguments:
  -h, --help            show this help message and exit
  --address ADDRESS     base address for ZMQ connections
  --log-address LOG_ADDRESS
                        Address to connect to global log
```

### Arguments

- ``--address``: Optional. The IP address of the machine the core
  script is executed on, prefixed with the ``tcp://`` protocol. The
  LArPix DAQ will automatically assign port 5551 to the core, so a port
  specification should not be included in ``--address``. The IP address
  specified here must be provided to any component which wants to connect
  to the core. Default: ``tcp://127.0.0.1`` (localhost)
- ``--log-address``: Optional. The IP address and port of the DAQ
  log object which the core should send its log messages to. Default:
  ``tcp://127.0.0.1:5678``

### Description

The core is responsible for managing and monitoring the DAQ system
components. This includes tracking which components are connected,
broadcasting the DAQ state, and sending operator commands to different
components.

The core must be the first script launched, since other components will
exit if they cannot connect to the core.

## Producer

Location: ``larpixdaq/producer.py``

Example invocation: ``python producer.py tcp://127.0.0.1:5001``

### Help text

```
usage: producer.py [-h] [--core CORE] [-d] [--fake] address

positional arguments:
  address

optional arguments:
  -h, --help   show this help message and exit
  --core CORE
  -d, --debug
  --fake
```

### Arguments

- ``address``: Required. The IP address and port of the machine running
  the producer script.
- ``--core``: Optional. The IP address of the DAQ core. Default:
  ``tcp://127.0.0.1`` (localhost)
- ``--debug``: Optional flag. When present, run in debug/verbose mode.
- ``--fake``: Optional flag. When present, use a larpix-control
  ``FakeIO`` object rather than communicating with an actual LArPix
  system.

### Description

The producer is the component with direct contact into the LArPix
environment. As such, the producer receives data from the data board and
sends it into the DAQ chain. It also sends configuration commands to the
LArPix ASICs and runs custom DAQ routines such as threshold scans and
calibrations.

Implementation-wise, this all happens via a larpix-control
``Controller`` object (not to be confused with the DAQ Controller).

Custom routines can be implemented by editing the
``larpixdaq/routines.py`` file (TODO!!! Make this more flexible). Custom
Routines are managed in a ``Routine`` object, in which you should store
the routine name, function handle/reference, and list of parameters.
(TODO!!! allow for documentation for custom routines.) Routines can
access the DAQ functionality via their arguments ``controller``,
``send_data``, ``send_info``. They can also accept additional arguments.
Routines must return a tuple of ``(controller, result)`` where
``result`` is the output of the routine (e.g. a list of thresholds, or
even simply the string ``"success"``) which must be JSON-serializable.

Operator/user interaction with the producer happens exclusively
through the LArPix DAQ Operator module. See the documentation for the
Operator module for available commands.

## Aggregator

Location: ``larpixdaq/aggregator.py``

Example invocation: ``python aggregator.py tcp://127.0.0.1:5002``

### Help text

```
usage: aggregator.py [-h] [-d] [--core CORE] address

positional arguments:
  address      the address to bind to

optional arguments:
  -h, --help   show this help message and exit
  -d, --debug
  --core CORE
```

### Arguments

- ``address``: Required. The IP address and port of the machine running
  the aggregator script.
- ``--debug``: Optional flag. When present, run in debug/verbose mode.
- ``--core``: Optional. The IP address of the DAQ core. Default:
  ``tcp://127.0.0.1`` (localhost)

### Description

The aggregator connects the producer (LArPix board) to any number of
data consumers such as data monitor and offline storage.

In the future, the aggregator will support receiving data from multiple
LArPix boards.
