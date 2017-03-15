#!/bin/bash

VENV=strecenv
PYVER=3.5

DEPARRAY=(numpy scipy matplotlib jupyter rasterio fiona xlrd xlwt pandas shapely h5py pytest pytest-cov pytables pytest-mpl obspy pyproj)

#if we're already in an environment called pager, switch out of it so we can remove it
source activate root
    
#remove any previous virtual environments called $VENV
CWD=`pwd`
cd $HOME;
conda remove --name $VENV --all -y
cd $CWD
    
#create a new virtual environment called $VENV with the below list of dependencies installed into it
conda create --name $VENV --yes --channel conda-forge python=$PYVER ${DEPARRAY[*]} -y

#install obspy separately, as it currently complains about python3.6
#conda install --no-deps --yes obspy

#activate the new environment
source activate $VENV

#download MapIO, install it using pip locally
curl --max-time 60 --retry 3 -L https://github.com/usgs/MapIO/archive/master.zip -o mapio.zip
pip install mapio.zip
rm mapio.zip

#download openquake, install it using pip locally, ignore specified dependencies,
#as these should be installed using conda above
curl --max-time 60 --retry 3 -L https://github.com/gem/oq-hazardlib/archive/master.zip -o openquake.zip
pip -v install --no-deps openquake.zip
rm openquake.zip

#tell the user they have to activate this environment
echo "Type 'source activate ${VENV}' to use this new virtual environment."
