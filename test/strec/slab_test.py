#!/usr/bin/env python
#stdlib imports
import os.path
import sys

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
repodir = os.path.abspath(os.path.join(homedir,'..','..'))
sys.path.insert(0,repodir) #put this at the front of the system path, ignoring any installed version of the repo

#local imports
from strec.slab import SlabCollection, GridSlab

#third party imports
import numpy as np


def test_grid_slab():
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    datadir = os.path.join(homedir,'..','..','strec','data','slabs') #all slabs should be here
    depthgrid = os.path.join(datadir,'kur_slab1_dep_01.01.12.grd')
    dipgrid = os.path.join(datadir,'kur_slab1_dip_01.01.12.grd')
    strgrid = os.path.join(datadir,'kur_slab1_str_01.01.12.grd')
    grid = GridSlab(depthgrid,dipgrid,strgrid,None)
    is_inside = grid.contains(40.0,140.0)
    assert is_inside

    slabinfo = grid.getSlabInfo(40.0,140.0)
    if not len(slabinfo):
        raise AssertionError('Slab results are empty!')
    cmp_dict = {'strike': 191.26111,
                'depth_uncertainty': 10,
                'region': 'kur',
                'dip': 25.959999084472656,
                'depth': 129.61000061035156}
    for key,value in cmp_dict.items():
        value2 = slabinfo[key]
        if isinstance(value,float):
            np.testing.assert_almost_equal(value,value2,decimal=4)
        else:
            assert value == value2
    
def test_inside_grid():
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    slabdir = os.path.join(homedir,'..','..','strec','data','slabs') 
    collection = SlabCollection(slabdir)
    lat = 10.0
    lon = 126.0
    depth = 0.0
    slabinfo = collection.getSlabInfo(lat,lon,depth)
    if not len(slabinfo):
        raise AssertionError('Slab results are empty!')
    test_slabinfo = {'region': 'phi',
                     'strike': 158.24164,
                     'dip': 45.32,
                     'depth': 55.900005340576172,
                     'depth_uncertainty':10.0,
                     }
    print('Testing against slab grid...')
    for key,value in slabinfo.items():
        assert key in test_slabinfo
        if isinstance(value,str):
            assert value == test_slabinfo[key]
        else:
            np.testing.assert_almost_equal(value,test_slabinfo[key],decimal=1)
    print('Passed.')

def test_inside_trench():
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    datadir = os.path.join(homedir,'..','data') #this should have one slab grid set and the trench file
    collection = SlabCollection(datadir)
    #rect_bounds = (132.83, 138.674, 31.11, 35.034)
    lat = 33.0
    lon = 132.0
    depth = 0.0
    slabinfo = collection.getSlabInfo(lat,lon,depth)
    test_slabinfo = {'region': 'AMlvPS',
                     'strike': 244.6,
                     'dip': 17.0,
                     'depth': 12.732043332893122,
                     'outside': False,
                     'slabtype': 'trench'}
    print('Testing against trench grid inside bounding box...')
    for key,value in slabinfo.items():
        assert key in test_slabinfo
        if isinstance(value,str):
            assert value == test_slabinfo[key]
        else:
            np.testing.assert_almost_equal(value,test_slabinfo[key],decimal=2)
    print('Passed.')

    #TODO: Find a point NOT inside bounding box, but inside buffered linestring
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
