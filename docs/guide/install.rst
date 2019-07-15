Installation
------------

LArPix DAQ can be installed from pip or from GitHub.

LArPix DAQ depends on HDF5 and h5py, which come with Anaconda
distributions but may need to be installed separately on other
distributions.

Default pip
installations on Macs require super-user privileges (``sudo``) for
installing new packages. This is a security risk which can be mitigated
by either

* using a Python 2 or 3 virtual environment
* using ``pip install --user XYZ``
* using Anaconda / conda

The following commands should be modified to accommodate whatever quirks
your pip installation comes with.

Virtual Environment
^^^^^^^^^^^^^^^^^^^

It is recommended
to create a virtual environment for your installation so that the
versions do not conflict with other projects you are working on. Python
virtualenvs do not always play well with Anaconda (although I haven't
had trouble, I have had auto-generated warnings), so if you have
Anaconda, use a conda environment rather than a virtualenv or venv.

Conda
"""""

In the below command, you can replace ``larpixdaq`` with whatever name
you want for your environment, and ``3.7`` with whatever version of
Python you want, though it is recommended to use Python 3::

    conda create --name larpixdaq python=3.7
    conda install -n larpixdaq pip

To activate the environment::

    conda activate larpixdaq

To deactivate::

    conda deactivate

To delete the environment::

    conda remove --name larpixdaq --all
    conda info --envs  # should not show larpixdaq environment

Python 3
""""""""

Move to a convenient directory, then run::

    python -m venv larpixdaq

To activate the environment::

    source larpixdaq/bin/activate

To deactivate::

    deactivate

Python 2
""""""""

Move to a convenient directory, then run::

    pip install virtualenv
    virtualenv larpixdaq

To activate the environment::

    source larpixdaq/bin/activate

To deactivate::

    deactivate

Getting LArPix DAQ
^^^^^^^^^^^^^^^^^^

Once you've activated your virtualenv, simply run::

    pip install larpix-daq

pip will download LArPix DAQ and all the prerequisites, including LArPix
Control and the xylem DAQ framework.
