#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='slic3r2aerotech',
    version='0.0.1',
    description='Convert Slic3r output into aerotech compatible gcode',
    author='Rodrigo Telles',
    author_email='rtelles@g.harvard.edu',
    url='https://github.com/rtellez700/slic3r2aerotech',
    packages=find_packages(include=['src.main.python', 'src.main.python.*']),
    package_dir={'slic3r2aerotech': 'src/main/python'}
)