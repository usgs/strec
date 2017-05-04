#!/usr/bin/env python

#stdlib imports
import os.path
import sys
import configparser

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
repodir = os.path.abspath(os.path.join(homedir,'..','..'))
datadir = os.path.join(homedir,'..','data') #test data files are here
sys.path.insert(0,repodir) #put this at the front of the system path, ignoring any installed version of the repo

#local imports
from strec.feregion import FERegions,get_focal_mechanism,inside_stable_region

#third party imports
import numpy as np
import fiona
import pandas as pd
from shapely.geometry import shape as tshape

CONFIG = {'constants':{'tplunge_rs':50,
                       'bplunge_ds':30,
                       'bplunge_ss':55,
                       'pplunge_nm':55,
                       'delplunge_ss':20,
                       'dstrike_interf':30,
                       'ddip_interf':30,
                       'dlambda':60,
                       'ddepth_interf':20,
                       'scr_dist':40,
                       'ddepth_intra':10,
                       'default_szdip':17,
                       'minradial_distcomp':0.5,
                       'maxradial_distcomp':1.0,
                       'step_distcomp':0.1,
                       'depth_rangecomp':10,
                       'minno_comp':3},
          'data':{'folder':datadir}}

def test_polygons():
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    datadir = os.path.join(homedir,'..','..','strec','data') #repository data files are here
    fepolygons = os.path.join(datadir,'fepolygons.json')
    print('Testing validity of all polygons...')
    with fiona.open(fepolygons,'r') as polygons:
        for polygon in polygons:
            shape = tshape(polygon['geometry'])
            rcode = polygon['properties']['regioncode']
            if not shape.is_valid:
                print('Shape %i is not valid' % rcode)
    print('Passed.')
    
def test_get_region():
    fereg = FERegions()

    #test simple polygon membership (no split)
    lat,lon = 21.40577,-78.046875
    depth = 15.0
    magnitude = 6.5
    print('Testing simple FE region membership...')
    reginfo = fereg.getRegion(lat,lon,depth,magnitude)
    test = {'FEGR': 85, 
            'NAME': ' CUBA REGION', 
            'TYPE': 21, 
            'SLABFLAG': '-', 
            'SCRFLAG': 0, 
            'SPLITFLAG': 0, 
            'H1': 35, 
            'REGIME1': 'ACRsh', 
            'H2': 85, 
            'REGIME2': 'ACRde', 
            'H3': '-', 
            'REGIME3': 'WARNING', 
            'REGIME_WARNING': 'ACRde', 
            'REGIME_TYPE': 'ACR (deep)'}
    assert reginfo == test
    regime,warning = fereg.getRegime(lat,lon,depth,magnitude,{},{},{})
    assert regime == 'ACRsh'
    print('Passed.')

    #test split polygon membership
    lat,lon = -51,163
    depth = 15.0
    magnitude = 6.5
    print('Testing split FE region membership...')
    reginfo = fereg.getRegion(lat,lon,depth,magnitude)
    test = {'FEGR': 166, 
            'NAME': ' AUCKLAND ISLANDS, N.Z. REGION', 
            'TYPE': 23, 
            'SLABFLAG': 'c', 
            'SCRFLAG': 0, 
            'SPLITFLAG': 1, 
            'REGIME_TYPE': 'ACR (oceanic boundary)', 
            'H1': 55, 
            'REGIME1': 'OBR', 
            'H2': '-', 
            'REGIME2': 'WARNING', 
            'H3': '-', 
            'REGIME3': '-', 
            'REGIME_WARNING': 'OBR'}
    assert reginfo == test
    regime,warning = fereg.getRegime(lat,lon,depth,magnitude,{},{},{})
    assert regime == 'OBR'
    print('Passed.')

    #test a region with sz stuff in it
    lat,lon = 13.300762,-88.725586
    depth = 15.0
    magnitude = 6.5
    config = {'constants':{'tplunge_rs':50,
                           'bplunge_ds':30,
                           'bplunge_ss':55,
                           'pplunge_nm':55,
                           'delplunge_ss':20,
                           'dstrike_interf':30,
                           'ddip_interf':30,
                           'dlambda':60,
                           'ddepth_interf':20,
                           'ddepth_intra':10}}
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
    slab_params = {'strike': 205.60037231445312, 
                   'depth': 91.38458251953125, 
                   'dip': 48.463893890380859}
    #testing a subduction zone event
    print('Testing subduction zone (should return crustal)...')
    regime,warning = fereg.getRegime(lat,lon,depth,magnitude,tensor_params,slab_params,config)
    assert regime == 'ACRsh'
    print('Passed.')

def test_regimes():
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    data_folder = os.path.join(homedir,'..','data') #repository data files are here
    config = {'constants':{'default_szdip':17,
                           'tplunge_rs':50,
                           'bplunge_ds':30,
                           'bplunge_ss':55,
                           'pplunge_nm':55,
                           'delplunge_ss':20,
                           'dstrike_interf':30,
                           'ddip_interf':30,
                           'dlambda':60,
                           'ddepth_interf':20,
                           'ddepth_intra':10,
                           'scr_dist': 40,
                           'minradial_distcomp':0.5,
                           'maxradial_distcomp':1.0,
                           'step_distcomp':0.1,
                           'depth_rangecomp':10,
                           'minno_comp':3},
              'data':{'folder':data_folder}}
    #this should turn out to be back-arc ACRsh
    lat,lon,depth,magnitude = (11.004219,124.678345,15.0,6.5)
    fereg = FERegions()
    reginfo = fereg.getRegimeInfo(lat,lon,depth,magnitude,config)
    

    
def test_focal_mechanism():
    config = {'constants':{'tplunge_rs':50,
                           'bplunge_ds':30,
                           'bplunge_ss':55,
                           'pplunge_nm':55,
                           'delplunge_ss':20,
                           'dstrike_interf':30,
                           'ddip_interf':30,
                           'dlambda':60,
                           'ddepth_interf':20,
                           'ddepth_intra':10}}
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
    assert get_focal_mechanism(tensor_params,config) == 'RS'

    #TODO:  Get other moment parameters for SS, NM, and ALL

    
def test_stable_regions():
    points = [((22.174688,45.878906),'ARA'),
              ((10.114894,20.566406),'AFR'),
              ((3.462703,44.604492),'SOM'),
              ((-20.841486,47.724609),'MDG'),
              ((-24.39213,135.527344),'AUS'),
              ((75.216657,141.328125),'SIB'),
              ((37.63816,-91.230469),'NOAM'),
              ((50.719069,37.265625),'EURAS'),
              ((40.341311,-4.438477),'IBE'),
              ((52.251346,-105.46875),'NOAM'),
              ((20.043031,-88.769531),'YUC'),
              ((-7.21535,-56.601562),'SAM'),
              ((23.054462,79.101563),'IND'),
              ((25.458155,114.082031),'CHI'),
              ((15.19276,104.72168),'SEAS')]
    for point in points:
        coords,rcode = point
        lat,lon = coords
        inside,rname,region_code,mindist = inside_stable_region(lat,lon)
        print('%s == %s' % (rcode,region_code))
        assert rcode == region_code

def test_all_regimes():
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    regime_file = os.path.join(homedir,'..','data','test_regimes.xlsx') #ends 2016-10-31
    df = pd.read_excel(regime_file)
    fereg = FERegions()
    for idx,row in df.iterrows():
        domain = row['Domain Name']
        lat = row['Lat']
        lon = row['Lon']
        depth = row['Depth']
        magnitude = row['Magnitude']
        regime = row['Tectonic Regime']
        try:
            results = fereg.getRegimeInfo(lat,lon,depth,CONFIG)
            print('Comparing domain %s and regime %s...' % (domain,regime))
            assert results['TectonicRegime'] == regime
            print('Passed.')
        except:
            print('Failed on domain %s, regime %s' % (domain,regime))
        

    
if __name__ == '__main__':
    test_all_regimes()
    # if len(sys.argv) > 1:
    #     grid_dir = sys.argv[1]
    #     test_all_regimes(grid_dir)
    # #test_get_region()
    # test_polygons()
    # test_focal_mechanism()
    # test_regimes()
    # test_stable_regions()
