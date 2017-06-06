#!/bin/bash

VENV=strecenv
PYVER=3.5

DEPARRAY=(numpy scipy matplotlib jupyter rasterio fiona gdal openpyxl xlrd xlwt pandas shapely h5py pytest pytest-cov pytables pytest-mpl obspy pyproj obspy)

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

#tell the user they have to activate this environment
echo "Type 'source activate ${VENV}' to use this new virtual environment."
