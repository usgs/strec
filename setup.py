#!/usr/bin/env python

from distutils.core import setup

setup(name='STREC',
      version='0.2',
      description='SeismoTectonic Regime Earthquake Calculator',
      author='Mike Hearne, Daniel Garcia',
      author_email='mhearne@usgs.gov, garciajimenez.d@gmail.com',
      url='https://github.com/usgs/strec/',
      packages=['strec'],
      scripts = ['strec.py','strec_init.py','strec_convert.py'],
      data_files=(os.path.expanduser('~'),['strec.ini']),
     )
