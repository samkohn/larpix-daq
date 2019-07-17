from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md')) as f:
    long_description = f.read()

with open(os.path.join(here, 'VERSION')) as f:
    version = f.read()


setup(
        name='larpix-daq',
        version=version,
        description='LArPix DAQ system',
        long_description=long_description,
        long_description_content_type='text/markdown',
        author='Sam Kohn, LBNL Neutrino Group',
        author_email='skohn@lbl.gov',
        keywords='dune larpix',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Science/Research',
            'Programming Language :: Python',
            'Topic :: Scientific/Engineering :: Physics',
            'Topic :: Scientific/Engineering',
            ],
        packages=find_packages(),
        install_requires=['xylem-daq', 'flask >=1.0.0', 'flask-socketio >=3.0',
            'eventlet >= 0.24', 'requests ~= 2.18',
            'larpix-control ~= 2.3.0'],
)
