#!/usr/bin/env python

# stdlib imports
import os.path
from collections import OrderedDict
from urllib.request import urlopen
import configparser
import json

# third party imports
import fiona
from shapely.geometry import shape as tshape
from shapely.geometry.point import Point
import pandas as pd
import numpy as np
from libcomcat.search import get_event_by_id

# local imports
from strec.subduction import SubductionZone
from strec.slab import SlabCollection
from strec.cmt import getCompositeCMT
from strec.proj import geo_to_utm
from strec.gmreg import Regionalizer
from strec.kagan import get_kagan_angle
from strec.tensor import fill_tensor_from_components
from strec.utils import get_config

EVENT_URL = 'https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=EVENTID&format=geojson'
SLAB_RAKE = 90  # presumed rake angle of slabs

SLAB_REGIONS = {'alu': 'Alaska-Aleutians',
                'cal': 'Calabria',
                'cam': 'Central America',
                'car': 'Caribbean',
                'cas': 'Cascadia',
                'cot': 'Cotabato',
                'hal': 'Halmahera',
                'hel': 'Helanic',
                'him': 'Himalaya',
                'hin': 'Hindu Kush',
                'izu': 'Izu-Bonin',
                'ker': 'Kermadec-Tonga',
                'kur': 'Kamchatka/Kurils/Japan',
                'mak': 'Makran',
                'man': 'Manila',
                'mex': 'Central America',
                'mue': 'Muertos',
                'pam': 'Pamir',
                'pan': 'Panama',
                'phi': 'Philippines',
                'png': 'New Guinea',
                'puy': 'Puysegur',
                'ryu': 'Ryukyu',
                'sam': 'South America',
                'sco': 'Scotia',
                'sol': 'Solomon Islands',
                'sul': 'Sulawesi',
                'sum': 'Sumatra-Java',
                'van': 'Santa Cruz Islands/Vanuatu/Loyalty Islands'}

CONSTANTS = {'tplunge_rs': 50,
             'bplunge_ds': 30,
             'bplunge_ss': 55,
             'pplunge_nm': 55,
             'delplunge_ss': 20}


class SubductionSelector(object):
    """For events that are inside a subduction zone, determine subduction zone properties.

    """

    def __init__(self):
        """Construct a SubductionSelector object.

        """
        self._regionalizer = Regionalizer.load()
        self._config = get_config()

    def getSubductionTypeByID(self, eventid):
        """Given an event ID, determine the subduction zone information.

        Args:
            eventid (str): ComCat EventID (Sumatra is official20041226005853450_30).
        Returns:
            Pandas Series object with indices:
                - TectonicRegion : (Subduction,Active,Stable,Volcanic)
                - TectonicDomain : SZ (generic)
                - FocalMechanism : (RS [Reverse],SS [Strike-Slip], NM [Normal], ALL [Unknown])
                - TensorType : (actual, composite)
                - KaganAngle : Angle between moment tensor and slab interface.
                - DistanceToStable : Distance in km from the nearest stable polygon.
                - DistanceToActive : Distance in km from the nearest active polygon.
                - DistanceToSubduction : Distance in km from the nearest subduction polygon.
                - DistanceToVolcanic : Distance in km from the nearest volcanic polygon.
                - Oceanic : Boolean indicating whether we are in an oceanic region.
                - DistanceToOceanic : Distance in km to nearest oceanic polygon.
                - DistanceToContinental : Distance in km to nearest continental polygon.
                - TectonicSubtype : (SZInter,ACR,SZIntra)
                - RegionContainsBackArc : Boolean indicating whether event is in a back-arc subduction region.
                - DomainDepthBand1 : Bottom of generic depth level for shallowest subduction type.
                - DomainDepthBand1Subtype : Shallowest subduction type.
                - DomainDepthBand2 : Bottom of generic depth level for middle subduction type.
                - DomainDepthBand2Subtype : Middle subduction type.
                - DomainDepthBand3 : Bottom of generic depth level for deepest subduction type.
                - DomainDepthBand3Subtype : Deepest subduction type
                - SlabModelRegion : Subduction region.
                - SlabModelType : (grid,trench)
                - SlabModelDepth : Depth to slab interface at epicenter.
                - SlabModelDip : Dip of slab at epicenter.
                - SlabModelStrike : Strike of slab at epicenter.
                - IsLikeInterface : Boolean indicating whether moment tensor strike is similar to interface.
                - IsNearInterface : Boolean indicating whether depth is close to interface.
                - IsInSlab : Boolean indicating whether depth is within the slab.

        """
        lat, lon, depth, tensor_params = self.getOnlineTensor(eventid)
        results = self.getSubductionType(
            lat, lon, depth, tensor_params=tensor_params)
        return results

    def getOnlineTensor(self, eventid):
        """Get tensor parameters from preferred ComCat moment tensor.

        Args:
            eventid (str): ComCat EventID (Sumatra is official20041226005853450_30).
        Returns:
            Moment tensor parameters dictionary:
                - source Moment Tensor source
                - type usually mww,mwc,mwb,mwr,TMTS or "unknown".
                - mrr,mtt,mpp,mrt,mrp,mtp Moment tensor components.
                - T T-axis values:
                  - azimuth
                  - plunge
                - N N-axis values:
                  - azimuth
                  - plunge
                - P P-axis values:
                  - azimuth
                  - plunge
                - NP1 First nodal plane values:
                  - strike
                  - dip
                  - rake
                - NP2 Second nodal plane values:
                  - strike
                  - dip
                  - rake
        """
        detail = get_event_by_id(eventid)
        lat = detail.latitude
        lon = detail.longitude
        depth = detail.depth
        if not detail.hasProduct('moment-tensor'):
            return lat, lon, depth, None

        tensor = detail.getProducts('moment-tensor')[0]
        tensor_params = {}
        btype = 'unknown'
        if tensor.hasProperty('derived-magnitude-type'):
            btype = tensor['derived-magnitude-type']
        elif tensor.hasProperty('beachball-type'):
            btype = tensor['beachball-type']
        if btype.find('/') > -1:
            btype = btype.split('/')[-1]
        tensor_params['type'] = btype
        tensor_params['source'] = tensor['eventsource'] + \
            '_' + tensor['eventsourcecode']

        tensor_params['mtt'] = float(tensor['tensor-mtt'])
        tensor_params['mpp'] = float(tensor['tensor-mpp'])
        tensor_params['mrr'] = float(tensor['tensor-mrr'])
        tensor_params['mtp'] = float(tensor['tensor-mtp'])
        tensor_params['mrt'] = float(tensor['tensor-mrt'])
        tensor_params['mrp'] = float(tensor['tensor-mrp'])

        T = {}
        T['value'] = float(tensor['t-axis-length'])
        T['plunge'] = float(tensor['t-axis-plunge'])
        T['azimuth'] = float(tensor['t-axis-azimuth'])
        tensor_params['T'] = T.copy()

        N = {}
        N['value'] = float(tensor['n-axis-length'])
        N['plunge'] = float(tensor['n-axis-plunge'])
        N['azimuth'] = float(tensor['n-axis-azimuth'])
        tensor_params['N'] = N.copy()

        P = {}
        P['value'] = float(tensor['p-axis-length'])
        P['plunge'] = float(tensor['p-axis-plunge'])
        P['azimuth'] = float(tensor['p-axis-azimuth'])
        tensor_params['P'] = P.copy()

        if not tensor.hasProperty('nodal-plane-1-strike'):
            tensor2 = fill_tensor_from_components(tensor_params['mrr'],
                                                  tensor_params['mtt'],
                                                  tensor_params['mpp'],
                                                  tensor_params['mrt'],
                                                  tensor_params['mrp'],
                                                  tensor_params['mtp'])
            tensor_params['NP1'] = tensor2['NP1'].copy()
            tensor_params['NP2'] = tensor2['NP2'].copy()
        else:
            NP1 = {}
            NP1['strike'] = float(tensor['nodal-plane-1-strike'])
            NP1['dip'] = float(tensor['nodal-plane-1-dip'])
            if 'nodal-plane-1-rake' in tensor.properties:
                NP1['rake'] = float(tensor['nodal-plane-1-rake'])
            else:
                NP1['rake'] = float(tensor['nodal-plane-1-slip'])
            tensor_params['NP1'] = NP1.copy()

            NP2 = {}
            NP2['strike'] = float(tensor['nodal-plane-2-strike'])
            NP2['dip'] = float(tensor['nodal-plane-2-dip'])
            if 'nodal-plane-2-rake' in tensor.properties:
                NP2['rake'] = float(tensor['nodal-plane-2-rake'])
            else:
                NP2['rake'] = float(tensor['nodal-plane-2-slip'])
            tensor_params['NP2'] = NP2.copy()

        return lat, lon, depth, tensor_params

    def getSubductionType(self, lat, lon, depth, eventid=None, tensor_params=None):
        """Given a event hypocenter, determine the subduction zone information.

        Args:
            lat (float): Epicentral latitude.
            lon (float): Epicentral longitude.
            depth (float): Epicentral depth.
            eventid (float): ComCat EventID (Sumatra is official20041226005853450_30).
            tensor_params (dict): Dictionary containing moment tensor parameters:
                - mrr,mtt,mpp,mrt,mrp,mtp Moment tensor components.
                - T T-axis values:
                  - azimuth
                  - plunge
                - N N-axis values:
                  - azimuth
                  - plunge
                - P P-axis values:
                  - azimuth
                  - plunge
                - NP1 First nodal plane values:
                  - strike
                  - dip
                  - rake
                - NP2 Second nodal plane values:
                  - strike
                  - dip
                  - rake
                (optional) - type Moment Tensor type.
                (optional) - source Moment Tensor source (regional network, name of study, etc.)
        Returns:
            Pandas Series object with indices:
                - TectonicRegion : (Subduction,Active,Stable,Volcanic)
                - TectonicDomain : SZ (generic)
                - FocalMechanism : (RS [Reverse],SS [Strike-Slip], NM [Normal], ALL [Unknown])
                - TensorType : (actual, composite)
                - KaganAngle : Angle between moment tensor and slab interface.
                - DistanceToStable : Distance in km from the nearest stable polygon.
                - DistanceToActive : Distance in km from the nearest active polygon.
                - DistanceToSubduction : Distance in km from the nearest subduction polygon.
                - DistanceToVolcanic : Distance in km from the nearest volcanic polygon.
                - Oceanic : Boolean indicating whether we are in an oceanic region.
                - DistanceToOceanic : Distance in km to nearest oceanic polygon.
                - DistanceToContinental : Distance in km to nearest continental polygon.
                - TectonicSubtype : (SZInter,ACR,SZIntra)
                - RegionContainsBackArc : Boolean indicating whether event is in a back-arc subduction region.
                - DomainDepthBand1 : Bottom of generic depth level for shallowest subduction type.
                - DomainDepthBand1Subtype : Shallowest subduction type.
                - DomainDepthBand2 : Bottom of generic depth level for middle subduction type.
                - DomainDepthBand2Subtype : Middle subduction type.
                - DomainDepthBand3 : Bottom of generic depth level for deepest subduction type.
                - DomainDepthBand3Subtype : Deepest subduction type
                - SlabModelRegion : Subduction region.
                - SlabModelType : (grid,trench)
                - SlabModelDepth : Depth to slab interface at epicenter.
                - SlabModelDip : Dip of slab at epicenter.
                - SlabModelStrike : Strike of slab at epicenter.
                - IsLikeInterface : Boolean indicating whether moment tensor strike is similar to interface.
                - IsNearInterface : Boolean indicating whether depth is close to interface.
                - IsInSlab : Boolean indicating whether depth is within the slab.
        """

        # sometimes events are specified with negative depths, which don't work with
        # our algorithms.  Pin those depths to 0.
        if depth < 0:
            depth = 0

        config = self._config
        slab_data_folder = config['DATA']['slabfolder']
        tensor_type = None
        tensor_source = None
        similarity = np.nan
        nevents = 0
        if tensor_params is None:
            if eventid is not None:
                tlat, tlon, tdep, tensor_params = self.getOnlineTensor(eventid)
                if tensor_params is not None:
                    tensor_type = tensor_params['type']
                    tensor_source = tensor_params['source']

            if tensor_params is None:
                dbfile = os.path.join(
                    config['DATA']['folder'], config['DATA']['dbfile'])
                minboxcomp = float(config['CONSTANTS']['minradial_distcomp'])
                maxboxcomp = float(config['CONSTANTS']['maxradial_distcomp'])
                dboxcomp = float(config['CONSTANTS']['step_distcomp'])
                depthboxcomp = float(config['CONSTANTS']['depth_rangecomp'])

                # Minimum number of events required to get composite mechanism
                nmin = int(config['CONSTANTS']['minno_comp'])
                tensor_params, similarity, nevents = getCompositeCMT(lat, lon, depth, dbfile,
                                                                     box=minboxcomp,
                                                                     depthbox=depthboxcomp,
                                                                     maxbox=maxboxcomp,
                                                                     dbox=dboxcomp, nmin=nmin)
                if tensor_params is not None:
                    tensor_type = 'composite'
                    tensor_source = 'composite'
        else:
            if 'type' in tensor_params:
                tensor_type = tensor_params['type']
            if 'source' in tensor_params:
                tensor_source = tensor_params['source']

        slab_collection = SlabCollection(slab_data_folder)
        slab_params = slab_collection.getSlabInfo(lat, lon, depth)

        reginfo = self._regionalizer.getRegions(lat, lon, depth)
        reginfo['TensorType'] = tensor_type
        reginfo['TensorSource'] = tensor_source
        reginfo['CompositeVariability'] = similarity
        reginfo['NComposite'] = nevents
        if len(slab_params):
            if np.isnan(slab_params['depth']):
                if tensor_params is not None:
                    reginfo['FocalMechanism'] = get_focal_mechanism(
                        tensor_params)
                results = reginfo.copy()
                results['SlabModelRegion'] = SLAB_REGIONS[slab_params['region']]
                results['KaganAngle'] = np.nan
                regizer = self._regionalizer
                domain = reginfo['TectonicDomain']
                results['TectonicSubtype'], _ = regizer.getSubDomain(
                    domain, depth)
            else:
                results = self._get_subduction_type(
                    lat, lon, depth, tensor_params, slab_params, reginfo, config)
                results['SlabModelRegion'] = SLAB_REGIONS[slab_params['region']]
                results['SlabModelDepth'] = slab_params['depth']
                results['SlabModelDepthUncertainty'] = slab_params['depth_uncertainty']
                results['SlabModelDip'] = slab_params['dip']
                results['SlabModelStrike'] = slab_params['strike']
                if tensor_params is not None:
                    np1 = tensor_params['NP1']
                    kagan = get_kagan_angle(slab_params['strike'], slab_params['dip'], SLAB_RAKE,
                                            np1['strike'], np1['dip'], np1['rake'])
                    results['KaganAngle'] = kagan
                else:
                    results['KaganAngle'] = np.nan
        else:
            results = reginfo.copy()
            results['FocalMechanism'] = get_focal_mechanism(tensor_params)
            results['SlabModelRegion'] = ''
            results['SlabModelDepth'] = np.nan
            results['SlabModelDepthUncertainty'] = np.nan
            results['SlabModelDip'] = np.nan
            results['SlabModelStrike'] = np.nan
            results['IsLikeInterface'] = False
            results['IsNearInterface'] = False
            results['IsInSlab'] = False
            results['KaganAngle'] = np.nan
            regizer = self._regionalizer
            domain = reginfo['TectonicDomain']
            results['TectonicSubtype'], _ = regizer.getSubDomain(domain, depth)

        results = results.reindex(index=['TectonicRegion', 'TectonicDomain', 'FocalMechanism',
                                         'TensorType', 'TensorSource', 'KaganAngle', 'CompositeVariability',
                                         'NComposite', 'DistanceToStable',
                                         'DistanceToActive', 'DistanceToSubduction',
                                         'DistanceToVolcanic', 'Oceanic',
                                         'DistanceToOceanic', 'DistanceToContinental',
                                         'TectonicSubtype', 'RegionContainsBackArc',
                                         'DomainDepthBand1', 'DomainDepthBand1Subtype',
                                         'DomainDepthBand2', 'DomainDepthBand2Subtype',
                                         'DomainDepthBand3', 'DomainDepthBand3Subtype',
                                         'SlabModelRegion',
                                         'SlabModelDepth',
                                         'SlabModelDepthUncertainty',
                                         'SlabModelDip', 'SlabModelStrike',
                                         'IsLikeInterface', 'IsNearInterface', 'IsInSlab'])

        return results

    def _get_subduction_type(self, lat, lon, depth,
                             tensor_params, slab_params, reginfo,
                             config):
        """Append subduction zone information to Regionalizer output.

        Args:
            lat (float): Epicentral latitude.
            lon (float): Epicentral longitude.
            depth (float): Epicentral depth.
            tensor_params (dict): Dictionary containing moment tensor parameters.
            slab_params (dict): Dictionary containing slab model parameters.
            reginfo (Series): Output from Regionalizer.getRegions().
            config (dict): Dictionary containing configuration information.
        Returns:
            Series: Indices appended to reginfo:
                - FocalMechanism 
                - IsLikeInterface
                - IsNearInterface
                - IsInSlab
                - TectonicSubtype
        """

        results = reginfo.copy()
        if depth <= reginfo['DomainDepthBand1']:
            depthzone = "shallow"
        elif depth > reginfo['DomainDepthBand1'] and depth <= reginfo['DomainDepthBand2']:
            depthzone = "medium"
        else:
            depthzone = "deep"
        fmstring = get_focal_mechanism(tensor_params)
        szinfo = SubductionZone(slab_params, tensor_params, depth, config)
        is_interface_like = szinfo.checkRupturePlane()
        is_near_interface = szinfo.checkInterfaceDepth()
        depth_band = reginfo['DomainDepthBand1']
        is_in_slab = szinfo.checkSlabDepth(depth_band)

        results['FocalMechanism'] = fmstring
        results['IsLikeInterface'] = is_interface_like
        results['IsNearInterface'] = is_near_interface
        results['IsInSlab'] = is_in_slab

        # get the bottom of the active crustal shallowest depth zone
        row = self._regionalizer.getDomainInfo('ACR (shallow)')
        acr_depth = row['H1']
        warning = ''
        # brace yourself, here's the sz flowchart...
        if depthzone == 'shallow':
            if fmstring == 'RS':
                if is_interface_like:  # eq. 2
                    if is_near_interface:
                        regime = 'SZInter'
                    else:
                        if is_in_slab:
                            regime = 'ACR'
                            warning = 'Event near/below interface'
                        else:
                            regime = 'ACR'
                else:
                    if is_in_slab:
                        regime = 'ACR'
                        warning = 'Event near/below interface'
                    else:
                        regime = 'ACR'
            else:  # fmstring is 'SS' or 'NM' or 'ALL'
                if fmstring == 'ALL' and tensor_params is None:
                    if is_near_interface:
                        regime = 'SZInter'
                        warning = 'No focal mechanism available'
                    else:
                        if is_in_slab:
                            regime = 'ACR'
                            warning = 'Event near/below interface'
                        else:
                            regime = 'ACR'
                else:
                    if is_in_slab:
                        regime = 'ACR'
                        warning = 'Event near/below interface'
                    else:
                        regime = 'ACR'
        elif depthzone == 'medium':
            if fmstring == 'RS':
                if is_interface_like:
                    if is_near_interface:
                        regime = 'SZInter'
                    else:
                        if is_in_slab:
                            regime = 'SZIntra'
                        else:
                            regime = 'ACR'
                else:
                    if is_in_slab:
                        regime = 'SZIntra'
                    else:
                        regime = 'ACR'
            else:
                if fmstring == 'ALL' and tensor_params is None:
                    if is_near_interface:
                        regime = 'SZInter'
                        warning = 'No focal mechanism available'
                    else:
                        if is_in_slab:
                            regime = 'SZIntra'
                        else:
                            regime = 'ACR'
                else:
                    if is_in_slab:
                        regime = 'SZIntra'
                    else:
                        regime = 'ACR'
        elif depthzone == 'deep':
            if is_in_slab:
                regime = 'SZIntra'
            else:
                warning = 'Event above interface'
                regime = 'SZIntra'

        results['TectonicSubtype'] = regime

        return results


def get_focal_mechanism(tensor_params):
    """ Return focal mechanism (strike-slip,normal, or reverse).

    Args:
        tensor_params (dict): Dictionary containing the following fields:
            - 'T' Dictionary of 'azimuth' and 'plunge' values for the T axis.
            - 'N' Dictionary of 'azimuth' and 'plunge' values for the N(B) axis.
            - 'P' Dictionary of 'azimuth' and 'plunge' values for the P axis.
            - 'NP1' Dictionary of angles for the first nodal plane ('strike','dip','rake')
            - 'NP2' Dictionary of angles for the second nodal plane ('strike','dip','rake')
        config (dict): dictionary containing: 
            - constants:
            - tplunge_rs
            - bplunge_ds
            - bplunge_ss
            - pplunge_nm
            - delplunge_ss
    Returns:
        str: Focal mechanism string 'SS','RS','NM',or 'ALL'.
    """
    if tensor_params is None:
        return 'ALL'
    # implement eq 1 here
    Tp = tensor_params['T']['plunge']
    Np = tensor_params['N']['plunge']
    Pp = tensor_params['P']['plunge']
    tplunge_rs = CONSTANTS['tplunge_rs']
    bplunge_ds = CONSTANTS['bplunge_ds']
    bplunge_ss = CONSTANTS['bplunge_ss']
    pplunge_nm = CONSTANTS['pplunge_nm']
    delplunge_ss = CONSTANTS['delplunge_ss']
    if Tp >= tplunge_rs and Np <= bplunge_ds:
        return 'RS'
    if Np >= bplunge_ss and (Tp >= Pp - delplunge_ss and Tp <= Pp + delplunge_ss):
        return 'SS'
    if Pp >= pplunge_nm and Np <= bplunge_ds:
        return 'NM'
    return 'ALL'
