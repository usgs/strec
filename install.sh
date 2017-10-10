#!/bin/bash
echo $PATH

VENV=strecenv
PYVER=3.5

# Is conda installed?
conda=$(which conda)
if [ ! "$conda" ] ; then
    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
        -O miniconda.sh;
    bash miniconda.sh -f -b -p $HOME/miniconda
    export PATH="$HOME/miniconda/bin:$PATH"
fi

# numpy scipy matplotlib jupyter rasterio fiona gdal openpyxl xlrd xlwt pandas shapely h5py pytest pytest-cov pytest-mpl obspy pyproj obspy

conda update -q -y conda
conda config --prepend channels conda-forge
conda config --append channels digitalglobe # for rasterio v 1.0a9
conda config --append channels ioos # for rasterio v 1.0a2

unamestr=`uname`
if [[ "$unamestr" == 'Linux' ]]; then
    DEPARRAY=(numpy=1.11 scipy=0.19.1 pyproj=1.9.5.1\
              pandas=0.20.3 openpyxl=2.5.0a1 xlrd=1.0.0 xlwt=1.2.0 \
              pytest=3.2.0 pytest-cov=2.5.1 fiona=1.7.8 h5py=2.7.0 \
              shapely=1.5.17 obspy=1.0.3 rasterio=1.0a2 gdal=2.1.4)
    
elif [[ "$unamestr" == 'FreeBSD' ]] || [[ "$unamestr" == 'Darwin' ]]; then
    DEPARRAY=(numpy=1.13.1 scipy=0.19.1 pyproj=1.9.5.1\
              pandas=0.20.3 openpyxl=2.5.0a1 xlrd=1.0.0 xlwt=1.2.0 \
              pytest=3.2.0 pytest-cov=2.5.1 fiona=1.7.8 h5py=2.7.0 \
              shapely=1.5.17 obspy=1.0.3 rasterio=1.0a9 gdal=2.1.4)
fi

# Is the Travis flag set?
travis=0
while getopts t FLAG; do
  case $FLAG in
    t)
      travis=1
      ;;
  esac
done

# Append additional deps that are not for Travis CI
if [ $travis == 0 ] ; then
    DEPARRAY+=(spyder=3.2.1 jupyter=1.0.0 \
        sphinx=1.6.3)
fi

# Turn off whatever other virtual environment user might be in
source deactivate

# Remove any previous virtual environments called shakelib2
CWD=`pwd`
cd $HOME;
conda remove --name $VENV --all -y
cd $CWD

# Create a conda virtual environment
echo "Creating the $VENV virtual environment"
echo "with the following dependencies:"
echo ${DEPARRAY[*]}
conda create --name $VENV -y python=$PYVER ${DEPARRAY[*]}

# Activate the new environment
echo "Activating the $VENV virtual environment"
source activate $VENV

# MapIO
echo "Installing MapIO..."
pip -q install https://github.com/usgs/MapIO/archive/master.zip

# libcomcat
echo "Installing MapIO..."
pip -q install https://github.com/usgs/libcomcat/archive/master.zip

# libcomcat
echo "Installing impactutils..."
pip -q install https://github.com/usgs/earthquake-impact-utils/archive/master.zip



# This package
echo "Installing strec..."
pip install -e .

# Tell the user they have to activate this environment
echo "Type 'source activate $VENV' to use this new virtual environment."
