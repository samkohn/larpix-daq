from setuptools import setup, find_packages

setup(
        name='larpixdaq',
        version='0.0.1',
        description='LArPix DAQ system',
        long_description='A DAQ system for LArPix built on xylem',
        author='Sam Kohn',
        author_email='skohn@lbl.gov',
        packages=find_packages(),
        install_requires=['xylem-daq', 'flask >=1.0.0', 'flask-socketio >=3.0',
            'eventlet >= 0.24', 'requests ~= 2.18',
            'larpix-control ~= 2.2'],
)
