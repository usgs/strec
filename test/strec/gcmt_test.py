#!/usr/bin/env python

from collections import OrderedDict
import numpy as np
from strec.gcmt import fetch_gcmt,ndk_to_dataframe
from datetime import datetime
import os.path

#remove later
from strec.subtype import get_focal_mechanism
from strec.tensor import fill_tensor_from_components

def throw_away():
    dataframe = fetch_gcmt()
    constants = {'tplunge_rs':50,
                 'bplunge_ds':30,
                 'bplunge_ss':55,
                 'pplunge_nm':55,
                 'delplunge_ss':20,
                 'dstrike_interf':30,
                 'ddip_interf':30,
                 'dlambda':60,
                 'ddepth_interf':20,
                 'ddepth_intra':10}
    config = {'CONSTANTS':constants}
    mechs = []
    for idx,row in dataframe.iterrows():
        tensor = fill_tensor_from_components(row['mrr'],row['mtt'],
                                             row['mpp'],row['mrt'],
                                             row['mrp'],row['mtp'])
        mech = get_focal_mechanism(tensor,config)
        mechs.append(mech)
    dataframe['focal_mechanism'] = mechs
    dataframe.to_excel('gcmt_mechanisms.xlsx')

def test_fetch_gcmt():
    dataframe = fetch_gcmt()
    first = dataframe.iloc[0]
    assert first['time'] == datetime(1976,1,1,1,29,39,600000)
    assert first['lat'] == -28.61
    print(first['mrr'])
    assert first['mrr'] == 7.68e+26
    random = dataframe.iloc[40000]
    assert random['time'] == datetime(2012,11,23,0,40,21,199999)
    assert random['lat'] == 1.62
    print(random['mrr'])
    assert random['mrr'] == 8.01e+22

def test_ndk_read():
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    ndkfile = os.path.join(homedir,'..','data','test.ndk')
    dataframe = ndk_to_dataframe(ndkfile)
    assert dataframe.iloc[0]['time'] == datetime(2017,1,1,14,12,8,99999)
    assert dataframe.iloc[0]['lat'] == 3.66
    assert dataframe.iloc[0]['mrr'] == 2.460000e+24

if __name__ == '__main__':
    throw_away()
    test_ndk_read()
    test_fetch_gcmt()
    
