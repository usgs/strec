#!/bin/bash

echo "Path:"
echo $PATH

VENV=strecenv

# Is the reset flag set?
reset=0
while getopts r FLAG; do
  case $FLAG in
    r)
        reset=1
        
      ;;
  esac
done

# Is conda installed?
conda=$(which conda)
if [ ! "$conda" ] ; then
    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
        -O miniconda.sh;
    bash miniconda.sh -f -b -p $HOME/miniconda
    export PATH="$HOME/miniconda/bin:$PATH"
fi

# Choose an environment file based on platform
unamestr=`uname`
if [ "$unamestr" == 'Linux' ]; then
    env_file=environment_linux.yml
elif [ "$unamestr" == 'FreeBSD' ] || [ "$unamestr" == 'Darwin' ]; then
    env_file=environment_osx.yml
fi

# If the user has specified the -r (reset) flag, then create an
# environment based on only the named dependencies, without
# any versions of packages specified.
if [ $reset eq 1 ]; then
    echo "Ignoring platform, letting conda sort out dependencies..."
    env_file=environment_basic.yml
fi

# Turn off whatever other virtual environment user might be in
source deactivate

# Download dependencies not in conda or pypi
curl --max-time 60 --retry 3 -L \
    https://github.com/usgs/earthquake-impact-utils/archive/master.zip -o impact-utils.zip
curl --max-time 60 --retry 3 -L \
    https://github.com/usgs/libcomcat/archive/master.zip -o libcomcat.zip
curl --max-time 60 --retry 3 -L \
    https://github.com/usgs/MapIO/archive/master.zip -o mapio.zip


# Create a conda virtual environment
echo "Creating the $VENV virtual environment:"
conda env create -f $env_file --force

# Bail out at this point if the conda create command fails.
# Clean up zip files we've downloaded
if [ $? -ne 0 ]; then
    echo "Failed to create conda environment.  Resolve any conflicts, then try again."
    echo "Cleaning up zip files..."
    rm impact-utils.zip
    rm libcomcat.zip
    rm mapio.zip
    exit
fi


# Activate the new environment
echo "Activating the $VENV virtual environment"
source activate $VENV

# Clean up downloaded packages
rm impact-utils.zip
rm libcomcat.zip
rm mapio.zip


# This package
echo "Installing strecenv..."
pip install -e .

# Tell the user they have to activate this environment
echo "Type 'source activate $VENV' to use this new virtual environment."
