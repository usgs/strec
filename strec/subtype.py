#!/usr/bin/env python

#stdlib imports
import os.path
from collections import OrderedDict
from urllib.request import urlopen
import configparser
import json

#third party imports
import fiona
from shapely.geometry import shape as tshape
from shapely.geometry.point import Point
import pandas as pd
import numpy as np
from libcomcat.search import get_event_by_id

#local imports
from .subduction import SubductionZone
from .slab import SlabCollection
from .cmt import getCompositeCMT
from .proj import geo_to_utm
from .gmreg import Regionalizer
from .kagan import get_kagan_angle
from .tensor import fill_tensor_from_components

EVENT_URL = 'https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=EVENTID&format=geojson'
SLAB_RAKE = 90 # presumed rake angle of slabs

SLAB_REGIONS = {'alu':'Alaska-Aleutians',
                'mex':'Central America',
                'cas':'Cascadia',
                'izu':'Izu-Bonin',
                'ker':'Kermadec-Tonga',
                'kur':'Kamchatka/Kurils/Japan',
                'phi':'Philippines',
                'ryu':'Ryukyu',
                'van':'Santa Cruz Islands/Vanuatu/Loyalty Islands',
                'sco':'Scotia',
                'sol':'Solomon Islands',
                'sam':'South America',
                'sum':'Sumatra-Java'}

CONSTANTS = {'tplunge_rs' : 50,
             'bplunge_ds' : 30,
             'bplunge_ss' : 55,
             'pplunge_nm' : 55,
             'delplunge_ss' : 20}
    
class SubductionSelector(object):
    def __init__(self):
        """For events that are inside a subduction zone, determine subduction zone properties.

        """
        self._regionalizer = Regionalizer.load()
        configfile = os.path.join(os.path.expanduser('~'),'.strec','strec.ini')
        if not os.path.isfile(configfile):
            raise Exception('Strec config file missing: supposed to be %s.' % configfile)
        self._config = configparser.ConfigParser()
        self._config.read(configfile)

    def getSubductionTypeByID(self,eventid):
        """Given an event ID, determine the subduction zone information.

        :param eventid:
          ComCat EventID (Sumatra is official20041226005853450_30).
        :returns:
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
            - SlabModelOutside : Boolean indicating whether the location is 
                                 in the undefined region of the slab.
            - SlabModelDepth : Depth to slab interface at epicenter.
            - SlabModelDip : Dip of slab at epicenter.
            - SlabModelStrike : Strike of slab at epicenter.
            - IsLikeInterface : Boolean indicating whether moment tensor strike is similar to interface.
            - IsNearInterface : Boolean indicating whether depth is close to interface.
            - IsInSlab : Boolean indicating whether depth is within the slab.

        """
        lat,lon,depth,tensor_params = self.getOnlineTensor(eventid)
        results = self.getSubductionType(lat,lon,depth,tensor_params=tensor_params)
        return results

    def getOnlineTensor(self,eventid):
        """Get tensor parameters from preferred ComCat moment tensor.
        
        :param eventid:
          ComCat EventID (Sumatra is official20041226005853450_30).
        :returns:
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
            return lat,lon,depth,None

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
        tensor_params['source'] = tensor['eventsource']+'_'+tensor['eventsourcecode']
        
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
        
        return lat,lon,depth,tensor_params

    def getSubductionType(self,lat,lon,depth,eventid=None,tensor_params=None):
        """Given an event ID, determine the subduction zone information.

        :param lat:
          Epicentral latitude.
        :param lon:
          Epicentral longitude.
        :param depth:
          Epicentral depth.
        :param eventid:
          ComCat EventID (Sumatra is official20041226005853450_30).
        :param tensor_params:
          Dictionary containing moment tensor parameters:
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
        :returns:
          Pandas Series object with indices:
            - TectonicRegion : (Subduction,Active,Stable,Volcanic)
            - TectonicDomain : SZ (generic)
            - FocalMechanism : (RS [Reverse],SS [Strike-Slip], NM [Normal], ALL [Unknown])
            - TensorType : (Mww,Mwb,Mwc,etc., or "composite")
            - TensorSource: Network and event ID or 'composite'.
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
            - SlabModelOutside : Boolean indicating whether the location is 
                                 in the undefined region of the slab.
            - SlabModelDepth : Depth to slab interface at epicenter.
            - SlabModelDip : Dip of slab at epicenter.
            - SlabModelStrike : Strike of slab at epicenter.
            - IsLikeInterface : Boolean indicating whether moment tensor strike is similar to interface.
            - IsNearInterface : Boolean indicating whether depth is close to interface.
            - IsInSlab : Boolean indicating whether depth is within the slab.
        """
        config = self._config
        data_folder = config['DATA']['folder']
        tensor_type = None
        tensor_source = None
        similarity = np.nan
        nevents = 0
        if tensor_params is None:
            if eventid is not None:
                tlat,tlon,tdep,tensor_params = self.getOnlineTensor(eventid)
                tensor_type = tensor_params['type']
                tensor_source = tensor_params['source']
            else:
                dbfile = os.path.join(config['DATA']['folder'],config['DATA']['dbfile'])
                minboxcomp = float(config['CONSTANTS']['minradial_distcomp'])
                maxboxcomp = float(config['CONSTANTS']['maxradial_distcomp'])
                dboxcomp = float(config['CONSTANTS']['step_distcomp'])
                depthboxcomp = float(config['CONSTANTS']['depth_rangecomp'])

                #Minimum number of events required to get composite mechanism
                nmin = int(config['CONSTANTS']['minno_comp'])
                tensor_params,similarity,nevents = getCompositeCMT(lat,lon,depth,dbfile,
                                                               box=minboxcomp,
                                                               depthbox=depthboxcomp,
                                                               maxbox=maxboxcomp,
                                                               dbox=dboxcomp,nmin=nmin)
                tensor_type = 'composite'
                tensor_source = 'composite'

        dip = config['CONSTANTS']['default_szdip']
        slab_collection = SlabCollection(data_folder,dip)
        slab_params = slab_collection.getSlabInfo(lat,lon)

        reginfo = self._regionalizer.getRegions(lat,lon,depth)
        reginfo['TensorType'] = tensor_type
        reginfo['TensorSource'] = tensor_source
        reginfo['CompositeVariability'] = similarity
        reginfo['NComposite'] = nevents
        if len(slab_params):
            if np.isnan(slab_params['depth']) or tensor_params is None:
                if slab_params['outside'] and reginfo['RegionContainsBackArc']:
                    #reclassify this as SZ back arc
                    reginfo['Domain'] = 'SZ (inland/back-arc)'
                    reginfo['TectonicSubtype'],regimeinfo = self._regionalizer.getSubType(reginfo['Domain'],depth)
                    reginfo['DomainDepthBand1Subtype'] = regimeinfo[0][0]
                    reginfo['DomainDepthBand1'] = regimeinfo[0][1]
                    reginfo['DomainDepthBand2Subtype'] = regimeinfo[1][0]
                    reginfo['DomainDepthBand2'] = regimeinfo[1][1]
                    reginfo['DomainDepthBand3Subtype'] = regimeinfo[2][0]
                    reginfo['DomainDepthBand3'] = regimeinfo[2][1]
                reginfo['FocalMechanism'] = get_focal_mechanism(tensor_params)
                results = reginfo.copy()
                results['KaganAngle'] = np.nan
            else:
                results = self._get_subduction_type(lat,lon,depth,tensor_params,slab_params,reginfo,config)
                results['SlabModelRegion'] = SLAB_REGIONS[slab_params['region']]
                results['SlabModelType'] = slab_params['slabtype']
                results['SlabModelOutside'] = slab_params['outside']
                results['SlabModelDepth'] = slab_params['depth']
                results['SlabModelDip'] = slab_params['dip']
                results['SlabModelStrike'] = slab_params['strike']
                np1 = tensor_params['NP1']
                kagan = get_kagan_angle(slab_params['strike'],slab_params['dip'],SLAB_RAKE,
                                        np1['strike'],np1['dip'],np1['rake'])
                results['KaganAngle'] = kagan
        else:
            results = reginfo.copy()
            results['FocalMechanism'] = get_focal_mechanism(tensor_params)
            results['SlabModelRegion'] = ''
            results['SlabModelType'] = ''
            results['SlabModelOutside'] = False
            results['SlabModelDepth'] = np.nan
            results['SlabModelDip'] = np.nan
            results['SlabModelStrike'] = np.nan
            results['IsLikeInterface'] = False
            results['IsNearInterface'] = False
            results['IsInSlab'] = False
            results['KaganAngle'] = np.nan

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
                                         'SlabModelRegion','SlabModelType',
                                         'SlabModelOutside','SlabModelDepth',
                                         'SlabModelDip','SlabModelStrike',
                                         'IsLikeInterface','IsNearInterface','IsInSlab' ])
            
        return results
        
    def _get_subduction_type(self,lat,lon,depth,
                            tensor_params,slab_params,reginfo,
                            config):
        
        results = reginfo.copy()
        if depth <= reginfo['DomainDepthBand1']:
            depthzone =  "shallow"
        elif depth > reginfo['DomainDepthBand1'] and depth <= reginfo['DomainDepthBand2']:
            depthzone = "medium"
        else:
            depthzone = "deep"
        fmstring = get_focal_mechanism(tensor_params)
        szinfo = SubductionZone(slab_params,tensor_params,depth,config)
        is_interface_like = szinfo.checkRupturePlane()
        is_near_interface = szinfo.checkInterfaceDepth()
        is_in_slab = szinfo.checkSlabDepth(reginfo['DomainDepthBand1'])

        results['FocalMechanism'] = fmstring
        results['IsLikeInterface'] = is_interface_like
        results['IsNearInterface'] = is_near_interface
        results['IsInSlab'] = is_in_slab

        #get the bottom of the active crustal shallowest depth zone
        row = self._regionalizer.getDomainInfo('ACR (shallow)')
        acr_depth = row['H1']
        warning = ''
        #brace yourself, here's the sz flowchart...
        if depthzone == 'shallow':
            if fmstring == 'RS':
                if is_interface_like: #eq. 2
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
            else: #fmstring is 'SS' or 'NM' or 'ALL'
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
                            if depth > acr_depth:
                                regime = 'ACR'
                            else:
                                regime = 'ACR'
                else:
                    if is_in_slab:
                        regime = 'SZIntra'
                    else:
                        if depth > acr_depth:
                            regime = 'ACR'
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
                            if depth > acr_depth:
                                regime = 'ACR'
                            else:
                                regime = 'ACR'
                else:
                    if is_in_slab:
                        regime = 'SZIntra'
                    else:
                        if depth > acr_depth:
                            regime = 'ACR'
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
    """
    Return focal mechanism (strike-slip,normal, or reverse).
    :param tensor_params: Dictionary containing the following fields:
           - 'T' Dictionary of 'azimuth' and 'plunge' values for the T axis.
           - 'N' Dictionary of 'azimuth' and 'plunge' values for the N(B) axis.
           - 'P' Dictionary of 'azimuth' and 'plunge' values for the P axis.
           - 'NP1' Dictionary of angles for the first nodal plane ('strike','dip','rake')
           - 'NP2' Dictionary of angles for the second nodal plane ('strike','dip','rake')
    :param config:
      dictionary containing:
       - constants:
         - tplunge_rs
         - bplunge_ds
         - bplunge_ss
         - pplunge_nm
         - delplunge_ss
    :returns: 
      String: 'SS','RS','NM','ALL'.
    """
    if tensor_params is None:
        return 'ALL'
    #implement eq 1 here
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
    if Np >= bplunge_ss and (Tp >= Pp-delplunge_ss and Tp <= Pp+delplunge_ss):
        return 'SS'
    if Pp >= pplunge_nm and Np <= bplunge_ds:
        return 'NM'
    return 'ALL'

