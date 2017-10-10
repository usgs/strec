#!/usr/bin/env python

from collections import OrderedDict
from strec.subtype import SubductionSelector,get_focal_mechanism
import pandas as pd
import numpy as np

def test_get_focal_mechanism():
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
        
    izmit_ss = {'T':{'azimuth':41,
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

    focal_ss = get_focal_mechanism(izmit_ss,config)
    assert focal_ss == 'SS'

    mexico_nm = {'T':{'azimuth':49,
                     'plunge':28},
                'N':{'azimuth':316,
                     'plunge':6},
                'P':{'azimuth':215,
                     'plunge':61},
                'NP1':{'strike':155,
                       'dip':18,
                       'rake':-70},
                'NP2':{'strike':315,
                       'dip':73,
                       'rake':-96}}
    focal_nm = get_focal_mechanism(mexico_nm,config)
    assert focal_nm == 'NM'

    northridge_rs = {'T':{'azimuth':107,
                          'plunge':81},
                     'N':{'azimuth':293,
                          'plunge':9},
                     'P':{'azimuth':202,
                          'plunge':1},
                     'NP1':{'strike':283,
                            'dip':45,
                            'rake':77},
                     'NP2':{'strike':122,
                            'dip':47,
                            'rake':103}}
    focal_rs = get_focal_mechanism(northridge_rs,config)
    assert focal_rs == 'RS'

    bogus_all =   {'T':{'azimuth':151,
                          'plunge':35.26},
                     'N':{'azimuth':4,
                          'plunge':35.26},
                     'P':{'azimuth':267,
                          'plunge':35.26},
                     'NP1':{'strike':326,
                            'dip':39,
                            'rake':45},
                     'NP2':{'strike':198,
                            'dip':64,
                            'rake':119}}
    focal_all = get_focal_mechanism(bogus_all,config)
    assert focal_all == 'ALL'

def test_get_online_tensor():
    eventid_with_tensor = 'official20110311054624120_30'
    eventid_without_tensor = 'us2000ati0'
    eventid_with_local_tensor = 'nc72852946'
    selector = SubductionSelector()
    lat1,lon1,depth1,tensor1 = selector.getOnlineTensor(eventid_with_tensor)
    lat2,lon2,depth2,tensor2 = selector.getOnlineTensor(eventid_without_tensor)
    lat3,lon3,depth3,tensor3 = selector.getOnlineTensor(eventid_with_local_tensor)
    x = 1

    
def test_subtype():
    # sumatra
    lat = 3.295
    lon = 95.982
    depth = 30.0
    eventid = 'official20041226005853450_30'
    tensor_params = {'mrr': 1.601e+22,
                     'mtt': -5.412e+21,
                     'mpp': -1.06e+22,
                     'mrt': 4.894e+22,
                     'mrp': -4.279e+22,
                     'mtp': 5.928e+21,
                     'NP1':{'strike': 335,
                             'dip': 7,
                             'rake': 113},
                     'NP2':{'strike': '131',
                             'dip': 83,
                             'rake': 87},
                     'T':{'value':6.797e+22,
                          'plunge':51,
                          'azimuth':38},
                     'N':{'value':-0.243e+22,
                          'plunge':3,
                          'azimuth':132},
                     'P':{'value':-6.554e+22,
                          'plunge':39,
                          'azimuth':224}}
    selector = SubductionSelector()
    results1 = selector.getSubductionType(lat,lon,depth)

    cmp_results1 = {'SlabModelStrike': 307.0806884765625,
                    'KaganAngle': 11.701047977452799,
                    'TectonicDomain': 'SZ (generic)',
                    'TensorSource': 'composite',
                    'DomainDepthBand1': 15,
                    'Oceanic': False,
                    'DomainDepthBand3Subtype': 'SZIntra',
                    'SlabModelOutside': False,
                    'DistanceToContinental': 0.0,
                    'CompositeVariability': np.nan,
                    'DistanceToOceanic': 573.60696079140143,
                    'DomainDepthBand1Subtype': 'ACR',
                    'SlabModelDepth': 38.658607482910156,
                    'IsInSlab': True,
                    'DistanceToVolcanic': 4741.4031661472618,
                    'RegionContainsBackArc': True,
                    'SlabModelType': 'grid',
                    'TensorType': 'composite',
                    'DomainDepthBand2Subtype': 'SZInter',
                    'DistanceToSubduction': 0.0,
                    'TectonicSubtype': 'SZInter',
                    'FocalMechanism': 'RS',
                    'IsLikeInterface': True,
                    'TectonicRegion': 'Subduction',
                    'DomainDepthBand3': 999,
                    'SlabModelRegion': 'Sumatra-Java',
                    'SlabModelDip': 20.450008392333984,
                    'DistanceToActive': 448.98577711531317,
                    'DomainDepthBand2': 70,
                    'IsNearInterface': True,
                    'NComposite': 48,
                    'DistanceToStable': 465.37340568412117}
    
    assert cmp_results1 == results1.to_dict()
    
    results2 = selector.getSubductionType(lat,lon,depth,eventid=eventid)

    cmp_results2 = {'IsNearInterface': True,
                    'CompositeVariability': np.nan,
                    'DistanceToSubduction': 0.0,
                    'SlabModelType': 'grid',
                    'TectonicSubtype': 'SZInter',
                    'TectonicRegion': 'Subduction',
                    'IsInSlab': True,
                    'DistanceToOceanic': 573.60696079140143,
                    'RegionContainsBackArc': True,
                    'Oceanic': False,
                    'KaganAngle': 15.246101829877405,
                    'DomainDepthBand2Subtype': 'SZInter',
                    'DomainDepthBand1Subtype': 'ACR',
                    'DistanceToVolcanic': 4741.4031661472618,
                    'SlabModelOutside': False,
                    'TensorSource': 'duputel_122604a',
                    'SlabModelDepth': 38.658607482910156,
                    'DomainDepthBand1': 15,
                    'NComposite': 0,
                    'SlabModelStrike': 307.0806884765625,
                    'DistanceToContinental': 0.0,
                    'DistanceToStable': 465.37340568412117,
                    'SlabModelDip': 20.450008392333984,
                    'SlabModelRegion': 'Sumatra-Java',
                    'TectonicDomain': 'SZ (generic)',
                    'DistanceToActive': 448.98577711531317,
                    'TensorType': 'Mww',
                    'DomainDepthBand3': 999,
                    'IsLikeInterface': True,
                    'FocalMechanism': 'RS',
                    'DomainDepthBand2': 70,
                    'DomainDepthBand3Subtype': 'SZIntra'}

    assert cmp_results2 == results2.to_dict()
    results3 = selector.getSubductionType(lat,lon,depth,tensor_params=tensor_params)

    cmp_results3 = {'DistanceToStable': 465.37340568412117,
                    'DomainDepthBand2Subtype': 'SZInter',
                    'DistanceToActive': 448.98577711531317,
                    'TensorSource': None,
                    'DomainDepthBand3Subtype': 'SZIntra',
                    'SlabModelOutside': False,
                    'RegionContainsBackArc': True,
                    'DistanceToContinental': 0.0,
                    'DistanceToVolcanic': 4741.4031661472618,
                    'FocalMechanism': 'RS',
                    'SlabModelStrike': 307.0806884765625,
                    'SlabModelType': 'grid',
                    'SlabModelRegion': 'Sumatra-Java',
                    'IsLikeInterface': True,
                    'TectonicRegion': 'Subduction',
                    'NComposite': 0,
                    'Oceanic': False,
                    'DomainDepthBand2': 70,
                    'CompositeVariability': np.nan,
                    'KaganAngle': 15.246101829877405,
                    'SlabModelDepth': 38.658607482910156,
                    'DistanceToOceanic': 573.60696079140143,
                    'IsInSlab': True,
                    'DomainDepthBand1Subtype': 'ACR',
                    'SlabModelDip': 20.450008392333984,
                    'TectonicDomain': 'SZ (generic)',
                    'TectonicSubtype': 'SZInter',
                    'DomainDepthBand3': 999,
                    'TensorType': None,
                    'IsNearInterface': True,
                    'DomainDepthBand1': 15,
                    'DistanceToSubduction': 0.0}
    assert cmp_results3 == results3.to_dict()

    #test a region NOT in a subduction zone
    lat,lon,depth = 39.053318,-104.765625,10.0
    results4 = selector.getSubductionType(lat,lon,depth)
    x = 1
    

def test_get_subduction_by_id():
    eventid = 'official20110311054624120_30'
    selector = SubductionSelector()
    results = selector.getSubductionTypeByID(eventid)
    cmpresults = {'KaganAngle': 15.371885896082663,
                  'DistanceToActive': 1084.2475225901173,
                  'SlabModelType': 'grid',
                  'DomainDepthBand2': 70,
                  'DistanceToContinental': 0.0,
                  'DomainDepthBand2Subtype': 'SZInter',
                  'TensorSource': None,
                  'DomainDepthBand3Subtype': 'SZIntra',
                  'SlabModelDepth': 30.23206329345703,
                  'SlabModelDip': 14.894770622253418,
                  'SlabModelOutside': False,
                  'RegionContainsBackArc': False,
                  'FocalMechanism': 'RS',
                  'DistanceToOceanic': 2966.5082894133589,
                  'SlabModelStrike': 190.22474670410156,
                  'TectonicRegion': 'Subduction',
                  'DistanceToStable': 491.91655794343046,
                  'IsInSlab': True,
                  'NComposite': 0,
                  'CompositeVariability': np.nan,
                  'TectonicSubtype': 'SZInter',
                  'IsLikeInterface': True,
                  'Oceanic': False,
                  'DomainDepthBand1Subtype': 'ACR',
                  'DistanceToSubduction': 0.0,
                  'TensorType': None,
                  'IsNearInterface': True,
                  'DistanceToVolcanic': 3663.5463981818389,
                  'TectonicDomain': 'SZ (on-shore)',
                  'SlabModelRegion': 'Kamchatka/Kurils/Japan',
                  'DomainDepthBand1': 15,
                  'DomainDepthBand3': 999}
    for key,value_cmp in cmpresults.items():
        value = results[key]
        if isinstance(value_cmp,float) and np.isnan(value_cmp):
            assert np.isnan(value)
        else:
            #print('Testing %s: %s and %s' % (key,str(value_cmp),str(value)))
            assert value_cmp == value
    
if __name__ == '__main__':
    test_get_online_tensor()
    test_get_subduction_by_id()
    test_get_focal_mechanism()
    test_subtype()
