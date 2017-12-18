#!/usr/bin/env python

from collections import OrderedDict
from strec.subtype import SubductionSelector,get_focal_mechanism
from strec.utils import get_config
from strec.gmreg import Regionalizer
import pandas as pd
import numpy as np

def reindex(results):
    results = results.reindex(index=['TectonicRegion','TectonicDomain','FocalMechanism',
                                     'TensorType','TensorSource','KaganAngle','CompositeVariability',
                                     'NComposite','DistanceToStable',
                                     'DistanceToActive','DistanceToSubduction',
                                     'DistanceToVolcanic','Oceanic',
                                     'DistanceToOceanic','DistanceToContinental',
                                     'TectonicSubtype','RegionContainsBackArc',
                                     'DomainDepthBand1','DomainDepthBand1Subtype',
                                     'DomainDepthBand2','DomainDepthBand2Subtype',
                                     'DomainDepthBand3','DomainDepthBand3Subtype',
                                     'SlabModelRegion',
                                     'SlabModelDepth',
                                     'SlabModelDepthUncertainty',
                                     'SlabModelDip','SlabModelStrike',
                                     'IsLikeInterface','IsNearInterface','IsInSlab' ])
    return results

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

def test_get_subduction_type():
    regionalizer = Regionalizer.load()
    # sumatra parameters
    lat = 3.295
    lon = 95.982
    depth = 30.0
    reginfo = regionalizer.getRegions(lat,lon,depth)
    selector = SubductionSelector()
    tensor_params = {'NP1':{'strike':336,
                            'dip':7,
                            'rake':114},
                     'NP2':{'strike':132,
                            'dip':84,
                            'rake':87},
                     'T':{'value':6.797e+22,'plunge':51,'azimuth':38},
                     'N':{'value':-0.243e+22,'plunge':3,'azimuth':132},
                     'P':{'value':-6.554e+22,'plunge':39,'azimuth':224}}
        
    slab_params = {'strike':307.0806884765625,
                   'dip':20.450008392333984,
                   'depth':38.658607482910156}

    #test a medium depth branch
    config = get_config()
    sub_info = selector._get_subduction_type(lat,lon,depth,
                            tensor_params,slab_params,reginfo,
                            config)
    assert sub_info['TectonicSubtype'] == 'SZInter'

    # test a shallow depth branch
    depth = 14.0
    sub_info = selector._get_subduction_type(lat,lon,depth,
                            tensor_params,slab_params,reginfo,
                            config)
    assert sub_info['TectonicSubtype'] == 'ACR'

    # test a deep depth branch
    depth = 100.0
    sub_info = selector._get_subduction_type(lat,lon,depth,
                            tensor_params,slab_params,reginfo,
                            config)
    assert sub_info['TectonicSubtype'] == 'SZIntra'

    # test a shallow depth branch with a moment tensor that is not interface like
    # this is a strike-slip tensor
    non_interface_ss_params = {'NP1':{'strike':241,
                                      'dip':79,
                                      'rake':173},
                               'NP2':{'strike':332,
                                      'dip':83,
                                      'rake':11},
                               'T':{'value':4.445e+18,'plunge':12,'azimuth':196},
                               'N':{'value':0.054e+18,'plunge':77,'azimuth':3},
                               'P':{'value':-4.499e+18,'plunge':3,'azimuth':106}}
    depth = 14.0
    sub_info = selector._get_subduction_type(lat,lon,depth,
                            non_interface_ss_params,slab_params,reginfo,
                            config)
    assert sub_info['TectonicSubtype'] == 'ACR'

    # test a shallow depth branch with a non-interface, RS MT
    non_interface_rs_params = {'NP1':{'strike':178,
                                      'dip':77,
                                      'rake':86},
                               'NP2':{'strike':17,
                                      'dip':14,
                                      'rake':108},
                               'T':{'value':2.236e+22,'plunge':58,'azimuth':82},
                               'N':{'value':0.040e+22,'plunge':4,'azimuth':179},
                               'P':{'value':-2.276e+22,'plunge':32,'azimuth':272}}
    sub_info = selector._get_subduction_type(lat,lon,depth,
                            non_interface_rs_params,slab_params,reginfo,
                            config)
    assert sub_info['TectonicSubtype'] == 'ACR'

    #test with a very shallow slab
    shallow_slab_params = {'strike':307.0806884765625,
                           'dip':20.450008392333984,
                           'depth':17.0}
    depth = 14.0
    sub_info = selector._get_subduction_type(lat,lon,depth,
                            tensor_params,shallow_slab_params,reginfo,
                            config)
    assert sub_info['TectonicSubtype'] == 'SZInter'

    # shallow, RS, like-interface,in slab
    shallow_slab_params = {'strike':307.0806884765625,
                           'dip':20.450008392333984,
                           'depth':-6.0}
    depth = 15.0
    sub_info = selector._get_subduction_type(lat,lon,depth,
                            tensor_params,shallow_slab_params,reginfo,
                            config)
    assert sub_info['TectonicSubtype'] == 'ACR'

    # shallow, RS, not-like-interface,in slab
    shallow_slab_params = {'strike':307.0806884765625,
                           'dip':20.450008392333984,
                           'depth':-6.0}
    depth = 15.0
    sub_info = selector._get_subduction_type(lat,lon,depth,
                            non_interface_rs_params,shallow_slab_params,reginfo,
                            config)
    assert sub_info['TectonicSubtype'] == 'ACR'

    # shallow, ALL (no moment tensor), near-interface
    non_interface_all_params = {'NP1':{'strike':313,
                                       'dip':61,
                                       'rake':152},
                                'NP2':{'strike':58,
                                       'dip':66,
                                       'rake':33},
                                'T':{'value':5.979e+19,'plunge':40,'azimuth':277},
                                'N':{'value':0.050e+19,'plunge':50,'azimuth':91},
                                'P':{'value':-6.030e+19,'plunge':3,'azimuth':185}}
    shallow_slab_params = {'strike':307.0806884765625,
                           'dip':20.450008392333984,
                           'depth':10.0}
    depth = 15.0
    sub_info = selector._get_subduction_type(lat,lon,depth,
                            None,shallow_slab_params,reginfo,
                            config)
    assert sub_info['TectonicSubtype'] == 'SZInter'

    # shallow, ALL (no moment tensor), in slab
    shallow_slab_params = {'strike':307.0806884765625,
                           'dip':20.450008392333984,
                           'depth':-6.0}
    depth = 15.0
    sub_info = selector._get_subduction_type(lat,lon,depth,
                            None,shallow_slab_params,reginfo,
                            config)
    assert sub_info['TectonicSubtype'] == 'ACR'

    # shallow, ALL (no moment tensor), above the interface
    shallow_slab_params = {'strike':307.0806884765625,
                           'dip':20.450008392333984,
                           'depth':25.0}
    depth = 0.0
    sub_info = selector._get_subduction_type(lat,lon,depth,
                            None,shallow_slab_params,reginfo,
                            config)
    assert sub_info['TectonicSubtype'] == 'ACR'


    # shallow, SS, in the slab
    shallow_slab_params = {'strike':307.0806884765625,
                           'dip':20.450008392333984,
                           'depth':-6.0}
    depth = 15
    sub_info = selector._get_subduction_type(lat,lon,depth,
                                             non_interface_ss_params,
                                             shallow_slab_params,
                                             reginfo,
                                             config)
    assert sub_info['TectonicSubtype'] == 'ACR'

    # medium, RS, interface-like, in slab
    depth = 30
    shallow_slab_params = {'strike':307.0806884765625,
                           'dip':20.450008392333984,
                           'depth':-6.0}
    sub_info = selector._get_subduction_type(lat,lon,depth,
                                             tensor_params,
                                             shallow_slab_params,
                                             reginfo,
                                             config)
    assert sub_info['TectonicSubtype'] == 'SZIntra'

    # medium, RS, interface-like, deep slab
    deep_slab_params = {'strike':307.0806884765625,
                        'dip':20.450008392333984,
                        'depth':50}
    depth = 16
    sub_info = selector._get_subduction_type(lat,lon,depth,
                                             tensor_params,
                                             deep_slab_params,
                                             reginfo,
                                             config)
    assert sub_info['TectonicSubtype'] == 'ACR'

    # medium, RS, not interface-like, in slab
    deep_slab_params = {'strike':307.0806884765625,
                        'dip':20.450008392333984,
                        'depth':30}
    depth = 65
    sub_info = selector._get_subduction_type(lat,lon,depth,
                                             non_interface_rs_params,
                                             deep_slab_params,
                                             reginfo,
                                             config)
    assert sub_info['TectonicSubtype'] == 'SZIntra'

    # medium, RS, not interface-like, in crust
    deep_slab_params = {'strike':307.0806884765625,
                        'dip':20.450008392333984,
                        'depth':55}
    depth = 20
    sub_info = selector._get_subduction_type(lat,lon,depth,
                                             non_interface_rs_params,
                                             deep_slab_params,
                                             reginfo,
                                             config)
    assert sub_info['TectonicSubtype'] == 'ACR'

    # medium, ALL (no MT), near interface
    deep_slab_params = {'strike':307.0806884765625,
                        'dip':20.450008392333984,
                        'depth':20}
    depth = 20
    sub_info = selector._get_subduction_type(lat,lon,depth,
                                             None,
                                             deep_slab_params,
                                             reginfo,
                                             config)
    assert sub_info['TectonicSubtype'] == 'SZInter'

    # medium, ALL (no MT), near interface
    deep_slab_params = {'strike':307.0806884765625,
                        'dip':20.450008392333984,
                        'depth':20}
    depth = 50
    sub_info = selector._get_subduction_type(lat,lon,depth,
                                             None,
                                             deep_slab_params,
                                             reginfo,
                                             config)
    assert sub_info['TectonicSubtype'] == 'SZIntra'

    # medium, ALL (no MT), in crust
    deep_slab_params = {'strike':307.0806884765625,
                        'dip':20.450008392333984,
                        'depth':55}
    depth = 20
    sub_info = selector._get_subduction_type(lat,lon,depth,
                                             None,
                                             deep_slab_params,
                                             reginfo,
                                             config)
    assert sub_info['TectonicSubtype'] == 'ACR'

    # medium, SS, in slab
    deep_slab_params = {'strike':307.0806884765625,
                        'dip':20.450008392333984,
                        'depth':20}
    depth = 50
    sub_info = selector._get_subduction_type(lat,lon,depth,
                                             non_interface_ss_params,
                                             deep_slab_params,
                                             reginfo,
                                             config)
    assert sub_info['TectonicSubtype'] == 'SZIntra'

    # medium, SS, in crust
    deep_slab_params = {'strike':307.0806884765625,
                        'dip':20.450008392333984,
                        'depth':55}
    depth = 20
    sub_info = selector._get_subduction_type(lat,lon,depth,
                                             non_interface_ss_params,
                                             deep_slab_params,
                                             reginfo,
                                             config)
    assert sub_info['TectonicSubtype'] == 'ACR'

    # deep, any MT, not in slab (interface or crustal)
    deep_slab_params = {'strike':307.0806884765625,
                        'dip':20.450008392333984,
                        'depth':110}
    depth = 75
    sub_info = selector._get_subduction_type(lat,lon,depth,
                                             tensor_params,
                                             deep_slab_params,
                                             reginfo,
                                             config)
    assert sub_info['TectonicSubtype'] == 'SZIntra'

    
    
    
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


    res,msg = cmp_dicts(tensor1,tensor1_cmp)
    res,msg = cmp_dicts(tensor3,tensor3_cmp)
    assert tensor2 is None

    
def test_subtype():
    selector = SubductionSelector()
    
    # sumatra
    lat = 3.295
    lon = 95.982
    depth = 30.0
    eventid = 'official20041226005853450_30'
    results1 = selector.getSubductionType(lat,lon,depth,eventid)
    assert results1['FocalMechanism'] == 'RS'
    assert results1['TectonicSubtype'] == 'SZInter'

    # northridge
    lat = 34.213
    lon = -118.537
    depth = 18.2
    eventid = 'ci3144585'
    results1 = selector.getSubductionType(lat,lon,depth,eventid)
    assert results1['FocalMechanism'] == 'RS'
    assert results1['TectonicSubtype'] == 'ACR'

    # landers
    lat = 34.200
    lon = -116.437
    depth = -0.1
    eventid = 'ci3031111'
    results1 = selector.getSubductionType(lat,lon,depth,eventid)
    assert results1['FocalMechanism'] == 'SS'
    assert results1['TectonicSubtype'] == 'ACR'

    # Made up event that should  have a composite moment tensor
    lat = 2.321
    lon = 128.132
    depth = 21.7
    results1 = selector.getSubductionType(lat,lon,depth)
    assert results1['TensorType'] == 'composite'
    assert results1['FocalMechanism'] == 'RS'
    assert results1['TectonicSubtype'] == 'SZInter'

    # Made up event that should not have a composite moment tensor
    lat = -27.725
    lon = -147.832
    depth = 25
    results1 = selector.getSubductionType(lat,lon,depth)
    assert results1['TectonicDomain'] == 'SOR (generic)'
    assert results1['FocalMechanism'] == 'ALL'
    assert results1['TectonicSubtype'] == 'SCR'

    # Pass in an event with tensor parameters
    # chile 2010
    lat = -36.122
    lon = -72.898
    depth = 22.9
    tensor_params = {'source':'duputel',
                     'type':'Mww',
                     'NP1':{'strike':178,
                            'dip':77,
                            'rake':86},
                     'NP2':{'strike':17,
                            'dip':14,
                            'rake':108},
                     'T':{'value':2.236e+22,'plunge':58,'azimuth':82},
                     'N':{'value':0.040e+22,'plunge':4,'azimuth':179},
                     'P':{'value':-2.276e+22,'plunge':32,'azimuth':272}}
    results1 = selector.getSubductionType(lat,lon,depth,eventid=None,
                                          tensor_params=tensor_params)
    assert results1['FocalMechanism'] == 'RS'

    # event location inside grid but not horizontally on subducting slab
    lat = 13.58
    lon = -92.92
    depth = 20.0
    results1 = selector.getSubductionType(lat,lon,depth)
    assert results1['TectonicSubtype'] == 'SZInter'
    assert results1['SlabModelRegion'] == 'Central America'
    
    
def test_get_subduction_by_id():
    selector = SubductionSelector()
    # Tohoku, should have an online moment tensor
    eventid = 'official20110311054624120_30'
    results = selector.getSubductionTypeByID(eventid)
    assert results['FocalMechanism'] == 'RS'
    assert results['TectonicSubtype'] == 'SZInter'
    assert results['SlabModelRegion'] == 'Kamchatka/Kurils/Japan'

def block_test_multiple_slabs():
    lat = 6.0
    lon = 125.0
    depth = 160
    selector = SubductionSelector()
    results = selector.getSubductionType(lat,lon,depth)
            
if __name__ == '__main__':
    test_get_focal_mechanism()
    test_get_subduction_type()
    test_subtype()
    test_get_subduction_by_id()
    # test_multiple_slabs()
    test_get_online_tensor()
    
    # 
