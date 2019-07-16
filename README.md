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
for response in o.run_routine('example'):
    print(response)
    # interact with response object within loop
# When the loop ends, the last response received is still saved in
# the response object
final_responses.append(response)
```
