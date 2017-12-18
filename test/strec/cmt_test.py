#!/usr/bin/env python
#stdlib imports
import os.path
import sys
import pprint

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
repodir = os.path.abspath(os.path.join(homedir,'..','..'))
sys.path.insert(0,repodir) #put this at the front of the system path, ignoring any installed version of the repo

#local imports
from strec.cmt import getCompositeCMT
from strec.subtype import get_focal_mechanism

#third party imports
import numpy as np
import pandas as pd

def test_composite():
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    dbfile = os.path.join(homedir,'..','data','strec.db') #ends 2016-10-31
    lat,lon,depth,magnitude = 3.295,95.982, 30.0, 9.1 #sumatra
    tensor_params1,similarity,N = getCompositeCMT(lat,lon,depth,dbfile,
                                                  box=0.5,depthbox=10.0,
                                                  nmin=3.0,maxbox=1.0,
                                                  dbox=0.1)

    testout = {'T': {'value': 0.90040807112868482,
                     'azimuth': 59.257592723523928,
                     'plunge': 60.956153671192382},
               'type': 'unknown',
               'NP1': {'rake': 99.706221357007934,
                       'dip': 72.880835583169542,
                       'strike': 135.04248070294602},
               'source': 'unknown',
               'N': {'value': 0.19843836648633859,
                     'azimuth': 312.16014237459842,
                     'plunge': 9.2722987641241801},
               'P': {'value': -1.0987962433960725,
                     'azimuth': 217.33561087867673,
                     'plunge': 27.25558260027913},
               'mrt': 0.5722075571696541,
               'mtp': 0.42166052289847422,
               'mpp': -0.056425346237488162,
               'mrr': 0.46289484505771517,
               'mtt': -0.40641930460127595,
               'NP2': {'rake': 61.304600053275323,
                       'dip': 19.607420050830289,
                       'strike': 284.8827314746506},
               'mrp': -0.57636593662837132}

    mechanism = get_focal_mechanism(tensor_params1)
    
    
    print('Testing that CMT composite tensor is consistent with past results...')
    assert mechanism == 'RS'
    for key,value in tensor_params1.items():
        value1 = testout[key]
        if isinstance(value,float):
            np.testing.assert_almost_equal(value,value1)
        elif isinstance(value,str):
            assert value == value1
        else:
            for key2,value2 in value.items():
                value3 = value1[key2]
                try:
                    np.testing.assert_almost_equal(value2,value3)
                except Exception as e:
                    print(key2,value2,value3)
                    raise e

    np.testing.assert_almost_equal(similarity,1.1036343285450121)
    assert N == 50
    print('Passed.')

if __name__ == '__main__':
    test_composite()

