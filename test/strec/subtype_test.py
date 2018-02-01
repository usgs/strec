#!/usr/bin/env python

from collections import OrderedDict
from strec.subtype import SubductionSelector, get_focal_mechanism
from strec.utils import get_config
from strec.gmreg import Regionalizer
import pandas as pd
import numpy as np


def reindex(results):
    results = results.reindex(index=['TectonicRegion', 'FocalMechanism',
                                     'TensorType', 'TensorSource', 'KaganAngle', 'CompositeVariability',
                                     'NComposite', 'DistanceToStable',
                                     'DistanceToActive', 'DistanceToSubduction',
                                     'DistanceToVolcanic', 'Oceanic',
                                     'DistanceToOceanic', 'DistanceToContinental',
                                     'SlabModelRegion',
                                     'SlabModelDepth',
                                     'SlabModelDepthUncertainty',
                                     'SlabModelDip', 'SlabModelStrike',
                                     ])
    return results


def cmp_dicts(dict1, dict2):
    missing1 = set(dict1.keys()) - set(dict2.keys())
    missing2 = set(dict2.keys()) - set(dict1.keys())
    if len(missing1) or len(missing2):
        return False, str(missing)
    # keys are identical, so look at values
    mismatched_keys = []
    for key, value in dict1.items():
        if isinstance(value, float) and np.isnan(value) and np.isnan(dict2[key]):
            continue
        if value != dict2[key]:
            mismatched_keys.append(key)
    if len(mismatched_keys):
        return False, str(mismatched_keys)
    return True, ''


def test_get_focal_mechanism():
    constants = {'tplunge_rs': 50,
                 'bplunge_ds': 30,
                 'bplunge_ss': 55,
                 'pplunge_nm': 55,
                 'delplunge_ss': 20,
                 'dstrike_interf': 30,
                 'ddip_interf': 30,
                 'dlambda': 60,
                 'ddepth_interf': 20,
                 'ddepth_intra': 10}
    config = {'CONSTANTS': constants}

    izmit_ss = {'T': {'azimuth': 41,
                      'plunge': 18},
                'N': {'azimuth': 237,
                      'plunge': 72},
                'P': {'azimuth': 133,
                      'plunge': 5},
                'NP1': {'strike': 178,
                        'dip': 74,
                        'rake': 9},
                'NP2': {'strike': 86,
                        'dip': 81,
                        'rake': 164}}

    focal_ss = get_focal_mechanism(izmit_ss)
    assert focal_ss == 'SS'

    mexico_nm = {'T': {'azimuth': 49,
                       'plunge': 28},
                 'N': {'azimuth': 316,
                       'plunge': 6},
                 'P': {'azimuth': 215,
                       'plunge': 61},
                 'NP1': {'strike': 155,
                         'dip': 18,
                         'rake': -70},
                 'NP2': {'strike': 315,
                         'dip': 73,
                         'rake': -96}}
    focal_nm = get_focal_mechanism(mexico_nm)
    assert focal_nm == 'NM'

    northridge_rs = {'T': {'azimuth': 107,
                           'plunge': 81},
                     'N': {'azimuth': 293,
                           'plunge': 9},
                     'P': {'azimuth': 202,
                           'plunge': 1},
                     'NP1': {'strike': 283,
                             'dip': 45,
                             'rake': 77},
                     'NP2': {'strike': 122,
                             'dip': 47,
                             'rake': 103}}
    focal_rs = get_focal_mechanism(northridge_rs)
    assert focal_rs == 'RS'

    bogus_all = {'T': {'azimuth': 151,
                       'plunge': 35.26},
                 'N': {'azimuth': 4,
                       'plunge': 35.26},
                 'P': {'azimuth': 267,
                       'plunge': 35.26},
                 'NP1': {'strike': 326,
                         'dip': 39,
                         'rake': 45},
                 'NP2': {'strike': 198,
                         'dip': 64,
                         'rake': 119}}
    focal_all = get_focal_mechanism(bogus_all)
    assert focal_all == 'ALL'

def test_get_online_tensor():
    eventid_with_tensor = 'official20110311054624120_30'
    eventid_without_tensor = 'us2000ati0'
    eventid_with_local_tensor = 'nc72852946'
    selector = SubductionSelector()
    lat1, lon1, depth1, tensor1 = selector.getOnlineTensor(eventid_with_tensor)
    lat2, lon2, depth2, tensor2 = selector.getOnlineTensor(
        eventid_without_tensor)
    lat3, lon3, depth3, tensor3 = selector.getOnlineTensor(
        eventid_with_local_tensor)
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

    res, msg = cmp_dicts(tensor1, tensor1_cmp)
    res, msg = cmp_dicts(tensor3, tensor3_cmp)
    assert tensor2 is None


def test_subtype():
    selector = SubductionSelector()

    # sumatra
    lat = 3.295
    lon = 95.982
    depth = 30.0
    eventid = 'official20041226005853450_30'
    results1 = selector.getSubductionType(lat, lon, depth, eventid)
    assert results1['FocalMechanism'] == 'RS'

    # northridge
    lat = 34.213
    lon = -118.537
    depth = 18.2
    eventid = 'ci3144585'
    results1 = selector.getSubductionType(lat, lon, depth, eventid)
    assert results1['FocalMechanism'] == 'RS'

    # landers
    lat = 34.200
    lon = -116.437
    depth = -0.1
    eventid = 'ci3031111'
    results1 = selector.getSubductionType(lat, lon, depth, eventid)
    assert results1['FocalMechanism'] == 'SS'

    # Made up event that should  have a composite moment tensor
    lat = 2.321
    lon = 128.132
    depth = 21.7
    results1 = selector.getSubductionType(lat, lon, depth)
    assert results1['TensorType'] == 'composite'
    assert results1['FocalMechanism'] == 'RS'

    # Made up event that should not have a composite moment tensor
    lat = -27.725
    lon = -147.832
    depth = 25
    results1 = selector.getSubductionType(lat, lon, depth)
    assert results1['FocalMechanism'] == 'ALL'

    # Pass in an event with tensor parameters
    # chile 2010
    lat = -36.122
    lon = -72.898
    depth = 22.9
    tensor_params = {'source': 'duputel',
                     'type': 'Mww',
                     'NP1': {'strike': 178,
                             'dip': 77,
                             'rake': 86},
                     'NP2': {'strike': 17,
                             'dip': 14,
                             'rake': 108},
                     'T': {'value': 2.236e+22, 'plunge': 58, 'azimuth': 82},
                     'N': {'value': 0.040e+22, 'plunge': 4, 'azimuth': 179},
                     'P': {'value': -2.276e+22, 'plunge': 32, 'azimuth': 272}}
    results1 = selector.getSubductionType(lat, lon, depth, eventid=None,
                                          tensor_params=tensor_params)
    assert results1['FocalMechanism'] == 'RS'

    # event location inside grid but not horizontally on subducting slab
    lat = 13.58
    lon = -92.92
    depth = 20.0
    results1 = selector.getSubductionType(lat, lon, depth)
    assert results1['SlabModelRegion'] == 'Central America'


def test_get_subduction_by_id():
    selector = SubductionSelector()
    # Tohoku, should have an online moment tensor
    eventid = 'official20110311054624120_30'
    results = selector.getSubductionTypeByID(eventid)
    assert results['FocalMechanism'] == 'RS'
    assert results['SlabModelRegion'] == 'Kamchatka/Kurils/Japan'


def block_test_multiple_slabs():
    lat = 6.0
    lon = 125.0
    depth = 160
    selector = SubductionSelector()
    results = selector.getSubductionType(lat, lon, depth)


if __name__ == '__main__':
    test_get_focal_mechanism()
    test_subtype()
    test_get_subduction_by_id()
    # test_multiple_slabs()
    test_get_online_tensor()

    #
