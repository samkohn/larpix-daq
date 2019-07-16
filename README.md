# larpix-daq

LArPix DAQ is the data acquisition system for LArPix. It handles the
data flow between the "data boards" and offline storage and includes
data monitoring and operator control functionality built on the xylem
DAQ framework.

LArPix DAQ consists of a set of scripts which are responsible for
individual parts of the DAQ system's functionality, as well as an
operator interface API which can be run in an interactive python session
or used as a basis for a more sophisticated interactive program. The
scripts can be run from the same or from different computers, as long as
the IP addresses of the various computers are known.


### System states

There are three states the system can be in: ``READY``, ``RUN``, and
``STOP``. The state is controlled through the ``Operator`` object using
the methods ``prepare_run`` (transition to ``READY``), ``begin_run``
(transition to ``START``), and ``end_run`` (transition to ``STOP``).

- ``STOP``: Default state on startup. All components are not expecting
  data.
- ``READY``: Components should prepare to receive data. Data may arrive
  at the component before the instruction to transition to the ``RUN``
  state (though this is expected to be rare). The component should treat
  that data as if it were received in the ``RUN`` state.
- ``RUN``: Components should expect to receive data. Data should not be
  produced in any other state.

To mark the start and end of a run in the data flow, the ``producer.py`` script
produces ``INFO`` messages with contents ``"Beginning run"`` and
``"Ending run"``, respectively.

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


## Run data

Location: ``larpixdaq/run_data.py``

Example invocation: ``python run_data.py``

### Help text

```
usage: run_data.py [-h] [--core CORE]

Launch the data consumer providing the online data monitor

optional arguments:
  -h, --help   show this help message and exit
  --core CORE  The address of the DAQ Core, not including port number
```

### Arguments

- ``--core``: Optional. The IP address of the DAQ core. Default:
  ``tcp://127.0.0.1`` (localhost)

### Description

Run data provides the online data monitor for the LArPix DAQ. It tracks
the packet rate and can send packets for manual inspection.

TODO!!! Make more properties available

## Offline data storage

Location: ``larpixdaq/offline_storage.py``

Example invocation: ``python offline_storage.py``

### Help text

```
usage: offline_storage.py [-h] [--core CORE]

Launch the data consumer to save LArPix data to disk

optional arguments:
  -h, --help   show this help message and exit
  --core CORE  The address of the DAQ Core, not including port number
```

### Arguments

- ``--core``: Optional. The IP address of the DAQ core. Default:
  ``tcp://127.0.0.1`` (localhost)

### Description

The offline storage script stores LArPix data to disk using the
LArPix+HDF5 file format.

## Operator

The LArPix DAQ Operator module provides the interface into the DAQ core
for all DAQ operations.

Operator methods interact with the DAQ core to accomplish the
desired behavior. For the simplest interactions, a single request
and response exchange occurs, and the result is returned.
(TODO!!! unify this interface) For most interactions, there are
multiple responses for a single request - e.g. an immediate
acknowledgement of receipt and then the eventual result. The
methods implementing these interactions return [generator
iterators](https://docs.python.org/3/glossary.html#term-generator)
rather than values. The way to call these functions usually looks like

```python
o = Operator()
final_responses = []
for response in o.run_routine('calibrate'):
    print(response)
    # interact with response object within loop
# When the loop ends, the last response received is still saved in
# the response object
final_responses.append(response)
```
