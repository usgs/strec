# stdlib imports
import os.path
import configparser
import re

# third party imports
import pandas as pd
import numpy as np

STRECINI = 'strec.ini'
GCMT_OUTPUT = 'gcmt.db'

CONSTANTS = {'minradial_disthist': 0.01,
             'maxradial_disthist': 1.0,
             'minradial_distcomp': 0.5,
             'maxradial_distcomp': 1.0,
             'step_distcomp': 0.1,
             'depth_rangecomp': 10,
             'minno_comp': 3,
             'default_szdip': 17,
             'dstrike_interf': 30,
             'ddip_interf': 30,
             'dlambda': 60,
             'ddepth_interf': 20,
             'ddepth_intra': 10}


def get_config_file_name():
    config_file = os.path.join(os.path.expanduser('~'), '.strec', 'strec.ini')
    return config_file


def get_config():
    """Get configuration information as a dictionary.

    'folder' should always be set to point to library data path.
    'dbfile' should be set to point to library data path unless specified in ~/.strec/strec.ini
    'slabfolder' should be set to point to library data path unless specified in ~/.strec/strec.ini

    Returns:
        config (dict): Dictionary containing fields:
            - CONSTANTS Dictionary containing constants for the application.
            - DATA Dictionary containing 'folder', 'slabfolder', and 'dbfile'.
    """
    # first look in the default path for a config file
    config_file = get_config_file_name()
    if os.path.isfile(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        if 'DATA' not in config:
            raise KeyError('STREC config file is missing the [DATA] section.')
    else:
        # if we didn't find one, then set the data stuff from the repo
        config = {'DATA': {}}

    homedir = os.path.dirname(os.path.abspath(__file__))  # where is this file?
    datafolder = os.path.abspath(os.path.join(homedir, 'data'))
    #automatically set path to json files, etc.
    config['DATA']['folder'] = datafolder
    if 'dbfile' not in config['DATA']:
        dbfile = 'moment_tensors.db'
        config['DATA']['dbfile'] = os.path.join(datafolder,dbfile)
        
    if 'slabfolder' not in config['DATA']:
        slabfolder = os.path.join(datafolder, 'slabs')
        config['DATA']['slabfolder'] = slabfolder

    if 'CONSTANTS' not in config:
        config['CONSTANTS'] = CONSTANTS
    return config


def read_input_file(input_file):
    """Read a CSV/Excel input file, return a DataFrame

    This function will deal with any moment tensor component columns it finds,
    (mrr,mtt,etc) and convert any that are integers into floats.

    Args:
        input_file (str): Path to CSV/Excel file containing lat,lon,depth columns
            and optionally moment tensor columns 
            ('mrr','mtt','mpp','mrt','mrp','mtp').
    Returns:
        DataFrame: Pandas dataframe containing contents of input file.
    Raises:
        ValueError: When input file is neither a CSV nor an Excel file.
    """
    df = None
    try:
        df = pd.read_csv(input_file)
    except:
        try:
            df = pd.read_excel(input_file)
        except:
            raise ValueError(
                '%s is neither a CSV nor Excel file.' % input_file)
    row_ok, msg = check_row(df.columns)
    if not row_ok:
        df = None

    # convert any long integer moment component columns to floating point, because
    # otherwise pandas will complain later when re-writing row to a dataframe.  Doesn't make
    # sense, but seems necessary.
    for column in df:
        comps = ['mrr', 'mtt', 'mpp', 'mrt', 'mrp', 'mtp']
        for comp in comps:
            if column.lower().find(comp) > -1:
                col = df[column].apply(lambda x: convert_float(x))
                df[column] = col

    return (df, msg)

def convert_float(val):
    try:
        return float(val)
    except ValueError:
        return np.nan


def check_row(row):
    """Ensure that input Series or Index has columns matching "lat","lon","depth".

    Args:
        row (Series): Pandas series object.
    Returns:
        tuple: (Boolean indicating whether row has valid columns,
            and a message, when False, indicating which column is missing.)
    """
    if isinstance(row, pd.core.indexes.base.Index):
        rowidx = row
    else:
        rowidx = row.index
    # row is a pandas series object
    if not rowidx.str.contains('^lat', case=False).any():
        return False, 'Missing "lat" column in input.'
    if not rowidx.str.contains('^lon', case=False).any():
        return False, 'Missing "lon" column in input.'
    if not rowidx.str.contains('^depth', case=False).any():
        return False, 'Missing "depth" column in input.'
    return (True, '')


def get_input_columns(row):
    """Return the latitude,longitude and depth columns from a Series.

    Args:
        row (Series): Pandas series object.
    Returns:
        tuple: (Name of latitude column,
                Name of longitude column,
                Name of depth column)
    """
    # row is a pandas series object
    lat = row[row.index.str.contains('^lat', case=False)][0]
    lon = row[row.index.str.contains('^lon', case=False)][0]
    depth = row[row.index.str.contains('^depth', case=False)][0]

    return (lat, lon, depth)


def render_row(row, format, lat, lon, depth):
    """Render a Series containing regselect output to the screen.

    Args:
        row (Series): Pandas series object.
        format (str): One of 'pretty','json','csv'.
        lat (float): Earthquake hypocentral latitude.
        lon (float): Earthquake hypocentral longitude.
        depth (float): Earthquake hypocentral depth.
    """
    if format == 'pretty':
        print('For event located at %.4f,%.4f,%.1f:' % (lat, lon, depth))
        for idx, value in row.iteritems():
            if re.match('^lat|^lon|^depth', idx, re.IGNORECASE):
                continue
            print('\t%s : %s' % (idx, str(value)))
        print()
    elif format == 'json':
        print(row.to_json())
    elif format == 'csv':
        values = [str(v) for v in row.values]
        print(','.join(values))
