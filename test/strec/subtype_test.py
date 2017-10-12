#!/usr/bin/env python

from collections import OrderedDict
from strec.subtype import SubductionSelector,get_focal_mechanism
import pandas as pd
import numpy as np

def cmp_dicts(dict1,dict2):
    missing1 = set(dict1.keys()) - set(dict2.keys())
    missing2 = set(dict2.keys()) - set(dict1.keys())
    if len(missing1) or len(missing2):
        return False,str(missing)
    #keys are identical, so look at values
    mismatched_keys = []
    for key,value in dict1.items():
        if isinstance(value,float) and np.isnan(value) and np.isnan(dict2[key]):
            continue
        if value != dict2[key]:
            mismatched_keys.append(key)
    if len(mismatched_keys):
        return False,str(mismatched_keys)
    return True,''

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

    focal_ss = get_focal_mechanism(izmit_ss)
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
    focal_nm = get_focal_mechanism(mexico_nm)
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
    focal_rs = get_focal_mechanism(northridge_rs)
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
    focal_all = get_focal_mechanism(bogus_all)
    assert focal_all == 'ALL'

def test_get_online_tensor():
    eventid_with_tensor = 'official20110311054624120_30'
    eventid_without_tensor = 'us2000ati0'
    eventid_with_local_tensor = 'nc72852946'
    selector = SubductionSelector()
    lat1,lon1,depth1,tensor1 = selector.getOnlineTensor(eventid_with_tensor)
    lat2,lon2,depth2,tensor2 = selector.getOnlineTensor(eventid_without_tensor)
    lat3,lon3,depth3,tensor3 = selector.getOnlineTensor(eventid_with_local_tensor)
    tensor1_cmp = {'T': {'value': 5.6e+22,
                         'plunge': 53.0,
                         'azimuth': 296.0},
                   'mtt': -1.509e+21,
                   'mpp': -1.523e+22,
                   'mrp': 4.837e+22,
                   'N': {'value': 1.2e+20,
                         'plunge': 1.0,
                         'azimuth': 204.0},
                   'mrr': 1.674e+22,
                   'mtp': -5.286e+21,
                   'P': {'value': -5.6e+22,
                         'plunge': 36.0,
                         'azimuth': 113.0},
                   'NP2': {'dip': 81.0,
                           'rake': 91.0,
                           'strike': 24.0},
                   'mrt': 2.243e+22,
                   'source': 'duputel_201103110546a',
                   'type': 'Mww',
                   'NP1': {'dip': 8.0,
                           'rake': 78.0,
                           'strike': 192.0}}
    tensor3_cmp = {'T': {'value': 8163000000000000.0,
                         'plunge': 8.605,
                         'azimuth': 77.715},
                   'mtt': -9703000000000000.0,
                   'mpp': 7235000000000000.0,
                   'mrp': -685500000000000.0,
                   'N': {'value': 2383000000000000.0,
                         'plunge': 80.784,
                         'azimuth': 278.857},
                   'mrr': 2468000000000000.0,
                   'mtp': -3748000000000000.0,
                   'P': {'value': -1.053e+16,
                         'plunge': 3.274,
                         'azimuth': 168.211},
                   'NP2': {'dip': 81.586203170542277,
                           'rake': 3.7979038011027644,
                           'strike': 213.24771227177959},
                   'mrt': 903300000000000.0,
                   'source': 'nc_72852946',
                   'type': 'Mw',
                   'NP1': {'dip': 86.243031559360034,
                           'rake': 171.5679508376947,
                           'strike': 122.69120043887619}}

    assert tensor1 == tensor1_cmp
    assert tensor2 is None
    assert tensor3 == tensor3_cmp
    

    
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
                    'KaganAngle': 10.896732671836423,
                    'TectonicDomain': 'SZ (generic)',
                    'TensorSource': 'composite',
                    'DomainDepthBand1': 15,
                    'Oceanic': False,
                    'DomainDepthBand3Subtype': 'SZIntra',
                    'SlabModelOutside': False,
                    'DistanceToContinental': 0.0,
                    'CompositeVariability': 1.1036343285450119,
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
                    'NComposite': 50,
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

    res,msg = cmp_dicts(results2.to_dict(),cmp_results2)
    assert res
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

    res,msg = cmp_dicts(results3.to_dict(),cmp_results3)
    assert res

    #test a region NOT in a subduction zone
    lat,lon,depth = 39.053318,-104.765625,10.0
    results4 = selector.getSubductionType(lat,lon,depth)

    cmp_results4 = {'SlabModelRegion': '',
                    'FocalMechanism': 'ALL',
                    'TensorType': 'composite',
                    'SlabModelOutside': False,
                    'KaganAngle': np.nan,
                    'DomainDepthBand3Subtype': 'SCR',
                    'TectonicRegion': 'Stable',
                    'TectonicSubtype': 'SCR',
                    'CompositeVariability': np.nan,
                    'DomainDepthBand1Subtype': 'SCR',
                    'SlabModelDip': np.nan,
                    'DistanceToOceanic': 1080.7850646123761,
                    'TectonicDomain': 'SCR (generic)',
                    'DistanceToStable': 0.0,
                    'NComposite': 0,
                    'SlabModelType': '',
                    'DistanceToActive': 52.3302278884006,
                    'DistanceToSubduction': 1085.9412247332527,
                    'IsNearInterface': False,
                    'IsInSlab': False,
                    'TensorSource': 'composite',
                    'DomainDepthBand1': 50,
                    'DomainDepthBand2Subtype': 'SCR',
                    'SlabModelDepth': np.nan,
                    'IsLikeInterface': False,
                    'DomainDepthBand2': 999,
                    'DistanceToContinental': 0.0,
                    'SlabModelStrike': np.nan,
                    'DistanceToVolcanic': 653.03283204758668,
                    'RegionContainsBackArc': False,
                    'DomainDepthBand3': 1000,
                    'Oceanic': False}
    
    res,msg = cmp_dicts(results4.to_dict(),cmp_results4)
    assert res
    

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
