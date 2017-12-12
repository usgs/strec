#!/usr/bin/env python

#stdlib imports
import os.path
import sys
import configparser

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
repodir = os.path.abspath(os.path.join(homedir,'..','..'))
sys.path.insert(0,repodir) #put this at the front of the system path, ignoring any installed version of the repo

#local imports
from strec.subduction import SubductionZone

#third party imports
import numpy as np
import fiona
from shapely.geometry import shape as tshape

def test_subduction():
    print('Testing subduction zone methods...')
    tensor_params = {'mrt': 0.5099597671251793, 
                     'mtp': -0.4243296978204512, 
                     'mrp': 0.047339378260129884, 
                     'mtt': -0.38465939943407423, 
                     'mrr': 0.295121465518152, 
                     'mpp': 0.08962038097418741,
                     'N': {'plunge': 16.194240791917125, 
                           'value': -0.025976686249628528, 
                           'azimuth': 301.68276190573891}, 
                     'P': {'plunge': 31.382272007754324, 
                           'value': -0.73756631821728935, 
                           'azimuth': 201.47904994724354}, 
                     'NP2': {'strike': 125.12249893161268, 
                             'rake': 106.54594789020415, 
                             'dip': 78.327237485658429}, 
                     'NP1': {'strike': 249.37817819831542, 
                             'rake': 35.958697855431353, 
                             'dip': 20.154468495374992}, 
                     'T': {'plunge': 53.791403813585845, 
                           'value': 0.76362545152518302, 
                           'azimuth': 55.053604171983046}}
    slab_params = {'strike': 295.60037231445312, 
                   'depth': 91.38458251953125, 
                   'dip': 48.463893890380859}
    depth = 15.0
    config = {'CONSTANTS':{'dstrike_interf':30,
                           'ddip_interf':30,
                           'dlambda':60,
                           'ddepth_interf':20,
                           'ddepth_intra':10}}
    szone = SubductionZone(slab_params,tensor_params,depth,config)
    assert szone.checkRupturePlane() == True
    assert szone.checkInterfaceDepth() == False
    assert szone.checkSlabDepth(15) == False
    print('Passed.')

    tensor_params2 = izmit_ss = {'T':{'azimuth':41,
                                      'plunge':18},
                                 'N':{'azimuth':237,
                                      'plunge':72},
                                 'P':{'azimuth':133,
                                      'plunge':5},
                                 'NP1':{'strike':178,
                                        'dip':74,
                                        'rake':9},
                                 'NP2':{'strike':86,
                                        'dip':81,
                                        'rake':164}}
    szone = SubductionZone(slab_params,tensor_params2,depth,config)
    assert szone.checkRupturePlane() == False
    assert szone.checkInterfaceDepth() == False
    assert szone.checkSlabDepth(15) == False
    
if __name__ == '__main__':
    test_subduction()

