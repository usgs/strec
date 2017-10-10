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

#third party imports
import numpy as np
import pandas as pd

def test_composite():
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    dbfile = os.path.join(homedir,'..','data','gcmt.db') #ends 2016-10-31
    lat,lon,depth,magnitude = 3.295,95.982, 30.0, 9.1 #sumatra
    tensor_params1,similarity,N = getCompositeCMT(lat,lon,depth,dbfile,
                                                  box=0.5,depthbox=10.0,
                                                  nmin=3.0,maxbox=1.0,
                                                  dbox=0.1)

    testout = {'source': 'unknown',
               'type': 'unknown',
               'NP1': {'rake': 100.52031312632604,
                       'dip': 73.243863248921315,
                       'strike': 135.03777341669905},
               'N': {'plunge': 10.068862832927204,
                     'azimuth': 311.97315442577172,
                     'value': 0.20904334788748433},
               'P': {'plunge': 27.506142553692584,
                     'azimuth': 216.66804033346173,
                     'value': -1.0801008480073353},
               'T': {'plunge': 60.407527752218563,
                     'azimuth': 60.193317264512899,
                     'value': 0.87104304622891504},
               
               'NP2': {'rake': 58.766321558510747,
                       'dip': 19.704433206482097,
                       'strike': 282.25043227746141},
               'mrr': 0.43463005982006192,
               'mtt': -0.40356317511779966,
               'mpp': -0.031081338593198435,
               'mrt': 0.56488318905497803,
               'mrp': -0.56202286423261294,
               'mtp': 0.41615798822834177}
    
    print('Testing that CMT composite tensor is consistent with past results...')
    assert tensor_params1 == testout
    assert similarity == 1.1662121199618094
    assert N == 47
    print('Passed.')

if __name__ == '__main__':
    test_composite()
    test_nodal_conversion()
