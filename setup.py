#!/usr/bin/env python

from distutils.core import setup
import os.path

STRECFOLDER = os.path.join(os.path.expanduser('~'), '.strec')
DATAFOLDER = os.path.join(os.path.expanduser('~'), '.strec', 'data')

setup(name='STREC',
      version='0.2',
      description='SeismoTectonic Regime Earthquake Calculator',
      author='Mike Hearne, Daniel Garcia',
      author_email='mhearne@usgs.gov, emthompson@usgs.gov, cbworden@usgs.gov',
      url='https://github.com/usgs/strec/',
      packages=['strec'],
      scripts=['bin/regselect', 'bin/subselect'],
      package_data={'strec': ['data/*.csv', 'data/*.txt',
                              'data/*.ini', 'data/*.json',
                              'data/*.geojson',
                              'data/*.db','data/*.xlsx',
                              'data/slabs/*.grd']},
      )
