from setuptools import setup, find_packages

setup(
        name='larpixdaq',
        version='0.0.1',
        description='LArPix DAQ system',
        long_description='A DAQ system for LArPix based on ModDAQ',
        author='Sam Kohn',
        author_email='skohn@lbl.gov',
        packages=find_packages(),
        install_requires=['moddaq']
)
