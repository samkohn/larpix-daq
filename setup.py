from setuptools import setup, find_packages

setup(
        name='larpixdaq',
        version='0.0.1',
        description='LArPix DAQ system',
        long_description='A DAQ system for LArPix based on ModDAQ',
        author='Sam Kohn',
        author_email='skohn@lbl.gov',
        packages=find_packages(),
        install_requires=['moddaq', 'flask >=1.0.0', 'flask-socketio >=3.0.0',
            'eventlet ~= 0.24.1', 'requests ~= 2.18'],
)
