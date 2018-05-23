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

unamestr=`uname`
if [ "$unamestr" == 'Linux' ]; then
    prof=~/.bashrc
    mini_conda_url=https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
    env_file=environment_linux.yml
elif [ "$unamestr" == 'FreeBSD' ] || [ "$unamestr" == 'Darwin' ]; then
    prof=~/.bash_profile
    mini_conda_url=https://repo.continuum.io/miniconda/Miniconda2-latest-MacOSX-x86_64.sh
    env_file=environment_osx.yml
else
    echo "Unsupported environment. Exiting."
    exit
fi

# Is conda installed?
conda --version
if [ $? -ne 0 ]; then
    echo "No conda detected, installing miniconda..."

    curl $mini_conda_url -o miniconda.sh;
    echo "Install directory: $HOME/miniconda"

    bash miniconda.sh -f -b -p $HOME/miniconda

    # Need this to get conda into path
    . $HOME/miniconda/etc/profile.d/conda.sh
else
    echo "conda detected, installing $VENV environment..."
fi

# If the user has specified the -r (reset) flag, then create an
# environment based on only the named dependencies, without
# any versions of packages specified.
if [ $reset == 1 ]; then
    echo "Ignoring platform, letting conda sort out dependencies..."
    env_file=environment.yml
fi

echo "Using ${env_file}"

# Turn off whatever other virtual environment user might be in
source deactivate

# Create a conda virtual environment
echo "Creating the $VENV virtual environment:"
conda env create -f $env_file --force

# Bail out at this point if the conda create command fails.
# Clean up zip files we've downloaded
if [ $? -ne 0 ]; then
    echo "Failed to create conda environment.  Resolve any conflicts, then try again."
    echo "Cleaning up zip files..."
    exit
fi


# Activate the new environment
echo "Activating the $VENV virtual environment"
source activate $VENV

# This package
echo "Installing strecenv..."
pip install -e .

# Tell the user they have to activate this environment
echo "Type 'source activate $VENV' to use this new virtual environment."
