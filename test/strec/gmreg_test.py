#!/usr/bin/env python

#stdlib imports
import os.path

from strec.gmreg import _get_nearest_point,_get_layer_info,Regionalizer
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon
import pandas as pd
import numpy as np

def test_nearest_point():
    point = Point(1,1)
    polygon = Polygon([(3,3),(3,5),(5,5),(5,3)])
    dist = _get_nearest_point(point,polygon)
    assert dist == 313.7054454693029

def test_layer_info():
    homedir = os.path.dirname(os.path.abspath(__file__))
    point = Point(-164.054,54.535)
    layer = 'Subduction'
    fname = os.path.abspath(os.path.join(homedir,'..','..','strec','data','subduction.json'))
    domain_field = 'REGIM_TYP'
    region,distance,domain,has_backarc = _get_layer_info(layer,point,
                                                          fname,
                                                          domain_field=domain_field)
    assert region == 'Subduction'
    assert distance == 61.233154384903926
    assert domain == 'SZ (generic)'
    assert has_backarc == True

def test_regionalizer():
    reg = Regionalizer.load()
    row = reg.getDomainInfo('SCR (generic)')
    assert row['TYPE'] == 10
    assert row['H1'] == 50
    assert row['SubDomain1'] == 'SCR'

    # this should fail
    try:
        row = reg.getDomainInfo('foo')
        assert 1 == 2
    except KeyError as ke:
        assert 1 == 1

    sub_domain,_ = reg.getSubDomain('SZ (generic)',25)
    assert sub_domain == 'SZInter'

    sub_domain,_ = reg.getSubDomain('SZ (generic)',100)
    assert sub_domain == 'SZIntra'

    region_series = reg.getRegions(0.0,5.14,25) # greenwich

    
    comp = {'TectonicRegion':'Stable',
           'TectonicDomain':'SOR (generic)',
           'DistanceToStable':0,
           'DistanceToActive':1574.06,
           'DistanceToSubduction':3358.47,
           'DistanceToVolcanic':95.7348,
           'Oceanic':False,
           'DistanceToOceanic':1574.06,
           'DistanceToContinental':0,
           'TectonicSubDomain':'SCR',
           'RegionContainsBackArc':False,
           'DomainDepthBand1':40,
           'DomainDepthBand1Subtype':'SCR',
           'DomainDepthBand2':999,
           'DomainDepthBand2Subtype':'SCR',
           'DomainDepthBand3':1000,
           'DomainDepthBand3Subtype':'SCR'}

    for key,value in comp.items():
        value2 = region_series[key]
        if isinstance(value,float):
            np.testing.assert_almost_equal(value,value2,decimal=1)
        else:
            assert value == value2

    region_series = reg.getRegions(-24.5,-14.2,25) # Southern Atlantic ocean
    x = 1
            
if __name__ == '__main__':
    test_nearest_point()
    test_layer_info()
    test_regionalizer()
