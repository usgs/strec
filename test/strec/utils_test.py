#!/usr/bin/env python

import os.path
import sys
from tempfile import mkdtemp, mkstemp
from strec.utils import (get_config, CONSTANTS,
                         get_config_file_name,
                         render_row, get_input_columns,
                         check_row, read_input_file)
from configparser import ConfigParser

import pandas as pd


def move_config():
    strec_config_file = get_config_file_name()
    tempfile = None
    if os.path.isfile(strec_config_file):
        tempdir = mkdtemp()
        tempfile = os.path.join(tempdir, 'strec.ini')
        os.rename(strec_config_file, tempfile)
    return tempfile


def restore_config(tempfile):
    strec_config_file = get_config_file_name()
    if tempfile is not None:
        tempdir, fname = os.path.split(tempfile)
        os.rename(tempfile, strec_config_file)
        os.rmdir(tempdir)


def get_config_dict(config):
    if not isinstance(config, dict):
        dictionary = {}
        for section in config.sections():
            dictionary[section] = {}
            for option in config.options(section):
                dictionary[section][option] = config.get(section, option)
    else:
        dictionary = config.copy()

    return dictionary


def test_get_config():
    # this tests a config file that may or may not be present
    # on a users system.  So, if one is there let's move it aside
    # so that testing is always consistent between systems.
    try:
        tempfile = move_config()
        config = get_config()
        dictionary = get_config_dict(config)
        assert sorted(list(dictionary.keys())) == ['CONSTANTS', 'DATA']
        cmp_options = ['maxradial_disthist',
                       'ddepth_intra',
                       'depth_rangecomp',
                       'ddepth_interf',
                       'maxradial_distcomp',
                       'dstrike_interf',
                       'minradial_distcomp',
                       'default_szdip',
                       'dlambda',
                       'minno_comp',
                       'step_distcomp',
                       'minradial_disthist',
                       'ddip_interf']
        assert sorted(cmp_options) == sorted(config['CONSTANTS'].keys())
    except Exception as e:
        raise(e)
    finally:
        restore_config(tempfile)

    if sys.platform == 'darwin':
        cfile = None
        try:
            tempfile = move_config()

            # create a config file
            config = ConfigParser()
            config['CONSTANTS'] = CONSTANTS
            cfile = get_config_file_name()
            with open(cfile, 'w') as configfile:
                config.write(configfile)

            # this will raise an exception
            config = get_config()

        except KeyError as ke:
            assert 1 == 1
        finally:
            if cfile is not None:
                os.remove(cfile)


def test_read_input_file():
    df = pd.DataFrame({'lat': [1, 2, 3],
                       'lon': [1, 2, 3],
                       'depth': [1, 2, 3]})
    tmpfile = None
    try:
        h, tmpfile = mkstemp(suffix='.xlsx')
        os.close(h)
        df.to_excel(tmpfile)
        read_input_file(tmpfile)
        df.to_csv(tmpfile)
        read_input_file(tmpfile)
        f = open(tmpfile, 'wb')
        barray = bytearray([123, 3, 255, 0, 100])
        f.write(barray)
        f.close()
        try:
            df2 = read_input_file(tmpfile)
        except ValueError as ve:
            assert 1 == 1
    except Exception as e:
        assert 1 == 2
    finally:
        if tmpfile is not None:
            os.remove(tmpfile)


def test_render_row():
    lat = 34.1
    lon = -118.1
    depth = 10.0
    row = pd.Series({'a': 1, 'b': 2.0, 'c': 'three'})
    for pformat in ['pretty', 'json', 'csv']:
        render_row(row, pformat, lat, lon, depth)


def test_get_input_columns():
    row = pd.Series({'lat': 1.0, 'lon': 2.0, 'depth': 3.0})
    lat, lon, depth = get_input_columns(row)
    row = pd.Series({'Latitude': 1.0, 'Longitude': 2.0, 'Depth': 3.0})
    lat, lon, depth = get_input_columns(row)


def test_check_row():
    row = pd.Series({'Latitude': 1.0, 'Longitude': 2.0, 'Depth': 3.0})
    false_row = pd.Series({'atitude': 1.0, 'ongitude': 2.0, 'epth': 3.0})

    res, msg = check_row(row)
    assert res
    res, msg = check_row(false_row)
    assert not res


if __name__ == '__main__':
    test_get_config()
    test_render_row()
    test_get_input_columns()
    test_check_row()
    test_read_input_file()
