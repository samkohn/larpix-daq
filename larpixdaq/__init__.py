"""The LArPix DAQ System records data from LArPix.

LArPix DAQ consists of a set of executable back-end modules, plus an
operator API. The system is built on top of the xylem DAQ framework. The
documentation here is intented to be self-contained.

Xylem allows for a networked DAQ system, where different components live
on different computers and send data and commands over the local network
and/or the Internet. This documentation will assume that all components
are being executed on the same machine, which will be referred to
by the loopback address 127.0.0.1. If you want to use the networked
functionality, simply replace 127.0.0.1 with the IP address of the
machine that the script is running on. Additionally, all scripts take
optional ``--core`` and ``--log-address`` arguments which default to ``tcp://127.0.0.1`` and
so will not be used in the documentation below. So you will need to pass
an explicit ``--core`` and/or ``--log-address`` argument with the IP address of the DAQ Core (if
it's not running on the same machine as the script), such as ``--core
tcp://labcomputer.university.edu``.

The suggested way to run all the scripts on one machine is to use
multiple terminals rather than sending scripts to the background, at
least until the software becomes stable.

Startup sequence
----------------

The first step is to launch the DAQ Log, which is a plain xylem module::

    python -m xylem.Log -p tcp://127.0.0.1:5678 -o log.txt

The ``-p`` argument lists the port to listen on (5678 is a convention
but not required), and ``-o`` give sthe location of the output file.
This Log script will print INFO-level messages and higher to stdout and
DEBUG-level messages and higher (i.e. all messages) to the output file.
To get all messages on stdout, simply start the log, then run ``tail
-f log.txt``, which will print each line of log.txt to stdout as it
arrives.

The DAQ Log is used for debugging and accountability purposes. It is not
intended to be particularly useful in day-to-day (production) operation.

The first "real" LArPix DAQ component to start is the DAQ Core, which
monitors and coordinates the other components::

    python -m larpixdaq.core

The rest of the DAQ components can be started in any order, but the
suggested order is the order of data flow::

    python -m larpixdaq.producer tcp://127.0.0.1:5001
    python -m larpixdaq.aggregator tcp://127.0.0.1:5002
    python -m larpixdaq.offline_storage
    python -m larpixdaq.online_monitor

Interacting with the DAQ
------------------------

All of these scripts are *not* interactive. All interactivity is
performed via an :py:class:`~operator.Operator` object, which can be scripted or
used in an interactive Python session as follows::

    from larpixdaq.operator import Operator
    op = Operator(core_IP_address)
    for response in op.prepare_physics_run():
        # do something with each response from the Core
        print(response)
    # do something with the final result, still saved as response
    print("Once again, the final result is:\\n", response)

The LArPix Webapp server uses this Operator API, so if you are using the
webapp you do not need to start your own Operator.

About port numbers
------------------

The command-line arguments for the DAQ scripts require you to specify
the port number for each component. By convention, the port numbers
should start at 5001 for the first component and then increment from
there. Only components which *send* data to other components need a
port number and IP address, which is why the offline storage and online
monitor don't get one.
"""
