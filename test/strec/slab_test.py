#!/usr/bin/env python
# stdlib imports
import os.path

# local imports
from strec.slab import SlabCollection, GridSlab

# third party imports
import numpy as np


def test_grid_slab():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datadir = os.path.join(homedir, '..', '..', 'strec',
                           'data', 'slabs')  # all slabs should be here
    depthgrid = os.path.join(datadir, 'kur_slab2_dep_02.24.18.grd')
    dipgrid = os.path.join(datadir, 'kur_slab2_dip_02.24.18.grd')
    strgrid = os.path.join(datadir, 'kur_slab2_str_02.24.18.grd')
    uncgrid = os.path.join(datadir, 'kur_slab2_unc_02.24.18.grd')
    grid = GridSlab(depthgrid, dipgrid, strgrid, uncgrid)
    is_inside = grid.contains(40.0, 140.0)
    assert is_inside

    slabinfo = grid.getSlabInfo(40.0, 140.0)
    if not len(slabinfo):
        raise AssertionError('Slab results are empty!')
    cmp_dict = {'dip': 28.817652,
                'depth': 127.33068084716797,
                'depth_uncertainty': 16.426598,
                'strike': 186.17316,
                'region': 'kur',
                'maximum_interface_depth': 57}
    for key, value in cmp_dict.items():
        value2 = slabinfo[key]
        if isinstance(value, float):
            np.testing.assert_almost_equal(value, value2, decimal=4)
        else:
            assert value == value2


def test_inside_grid():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    slabdir = os.path.join(homedir, '..', '..', 'strec', 'data', 'slabs')
    collection = SlabCollection(slabdir)
    lat = 10.0
    lon = 126.0
    depth = 0.0
    slabinfo = collection.getSlabInfo(lat, lon, depth)
    if not len(slabinfo):
        raise AssertionError('Slab results are empty!')
    test_slabinfo = {'maximum_interface_depth': 53,
                     'depth': 67.86959075927734,
                     'strike': 159.2344,
                     'dip': 45.410145,
                     'depth_uncertainty': 14.463925,
                     'region': 'phi'}
    print('Testing against slab grid...')
    for key, value in slabinfo.items():
        assert key in test_slabinfo
        if isinstance(value, str):
            assert value == test_slabinfo[key]
        else:
            np.testing.assert_almost_equal(
                value, test_slabinfo[key], decimal=1)
    print('Passed.')


def test_inside_trench():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    # this should have one slab grid set and the trench file
    datadir = os.path.join(homedir, '..', 'data')
    collection = SlabCollection(datadir)
    #rect_bounds = (132.83, 138.674, 31.11, 35.034)
    lat = 33.0
    lon = 132.0
    depth = 0.0
    slabinfo = collection.getSlabInfo(lat, lon, depth)
    test_slabinfo = {'region': 'AMlvPS',
                     'strike': 244.6,
                     'dip': 17.0,
                     'depth': 12.732043332893122,
                     'outside': False,
                     'slabtype': 'trench'}
    print('Testing against trench grid inside bounding box...')
    for key, value in slabinfo.items():
        assert key in test_slabinfo
        if isinstance(value, str):
            assert value == test_slabinfo[key]
        else:
            np.testing.assert_almost_equal(
                value, test_slabinfo[key], decimal=2)
    print('Passed.')

    # TODO: Find a point NOT inside bounding box, but inside buffered linestring
    # lat = 31.108
    # lon = 132.828
    # #buffer_bounds = (132.8276056605721, 31.107939894159855, 138.67648615178288, 35.0360448932795)
    # slabinfo = collection.getSlabInfo(lat,lon)
    # test_slabinfo = {'region': 'AMlvPS',
    #                  'strike': 244.6,
    #                  'dip': 17.0,
    #                  'depth': 12.732043332893122,
    #                  'outside': False,
    #                  'slabtype': 'trench'}
    # print('Testing against trench grid outside bounding box...')
    # for key,value in slabinfo.items():
    #     assert key in test_slabinfo
    #     if isinstance(value,str):
    #         assert value == test_slabinfo[key]
    #     else:
    #         np.testing.assert_almost_equal(value,test_slabinfo[key],decimal=2)
    # print('Passed.')


def test_outside_grid():
    pass


if __name__ == '__main__':
    test_inside_grid()
    test_inside_trench()
    test_outside_grid()
    test_grid_slab()
