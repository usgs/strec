#!/usr/bin/env python
#stdlib imports
import os.path
import sys

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
repodir = os.path.abspath(os.path.join(homedir,'..','..'))
sys.path.insert(0,repodir) #put this at the front of the system path, ignoring any installed version of the repo

#local imports
from strec.cmt import getCompositeCMT,get_tensor_params_from_nodal

#third party imports
import numpy as np
import pandas as pd

def test_nodal_conversion():
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    excelfile = os.path.join(homedir,'..','data','large_events.xlsx')
    df = pd.read_excel(excelfile)
    for idx,row in df.iterrows():
        strike = row['Strike']
        dip = row['Dip']
        rake = row['Rake']
        mag = row['Magnitude']
        if np.isnan(strike):
            continue
        
        tensor_params = get_tensor_params_from_nodal(strike,dip,rake,mag)
        

def test_composite():
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    dbfile = os.path.join(homedir,'..','data','gcmt.db') #ends 2016-10-31
    lat,lon,depth,magnitude = 3.295,95.982, 30.0, 9.1 #sumatra
    tensor_params,warning = getCompositeCMT(lat,lon,depth,dbfile,box=0.5,depthbox=10.0,nmin=3.0,maxbox=1.0,dbox=0.1)
    testout = {'mrt': 0.6240629689002251, 
               'mrr': 0.4512905515294056,
               'mpp': -0.05681854135935799,
               'mtt': -0.39450158699121396,
               'mtp': -0.7037801896771995, 
               'mrp': 0.35043108787496347,
               'N': {'plunge': 10.054848444412581, 
                     'value': 0.11535119529116966, 
                     'azimuth': 314.80481530618238}, 
               'P': {'plunge': 30.184620055622009, 
                     'value': -1.1434359674210017, 
                     'azimuth': 218.8850532017122}, 
               'T': {'plunge': 57.843183531128417, 
                     'value': 1.0280551953086663, 
                     'azimuth': 61.186893050145962}, 
               'NP2': {'strike': 280.3843393831188, 
                       'dip': 17.41586211850997, 
                       'rake': 54.315541625718268},  
               'NP1': {'strike': 137.35186280187526, 
                       'dip': 75.929950446208395, 
                       'rake': 100.36921815024265}}
    print('Testing that CMT composite tensor is consistent with past results...')
    assert tensor_params == testout
    print('Passed.')
    
if __name__ == '__main__':
    test_composite()
    test_nodal_conversion()
