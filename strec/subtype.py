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

#local imports
from .subduction import SubductionZone
from .slab import SlabCollection
from .cmt import getCompositeCMT
from .proj import geo_to_utm
from .comcat import ComCat
from .gmreg import Regionalizer

EVENT_URL = 'https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=EVENTID&format=geojson'

class SubductionSelector(object):
    def __init__(self):
        self._regionalizer = Regionalizer.load()
        configfile = os.path.join(os.path.expanduser('~'),'.strec','strec.ini')
        if not os.path.isfile(configfile):
            raise Exception('Strec config file missing: supposed to be %s.' % configfile)
        self._config = configparser.ConfigParser()
        self._config.read(configfile)
        self._comcat = ComCat()

    def getSubductionTypeByID(self,eventid):
        lat,lon,depth,tensor_params = self._comcat.getEventProperties(eventid)
        results = self.getSubductionType(lat,lon,depth,tensor_params=tensor_params)
        return results
        

    def getSubductionType(self,lat,lon,depth,tensor_params=None):
        config = self._config
        data_folder = config['DATA']['folder']
        if tensor_params is None:
            dbfile = os.path.join(data_folder,'gcmt.db')
            minboxcomp = float(config['CONSTANTS']['minradial_distcomp'])
            maxboxcomp = float(config['CONSTANTS']['maxradial_distcomp'])
            dboxcomp = float(config['CONSTANTS']['step_distcomp'])
            depthboxcomp = float(config['CONSTANTS']['depth_rangecomp'])

            #Minimum number of events required to get composite mechanism
            nmin = int(config['CONSTANTS']['minno_comp'])
            tensor_params,tensor_warning = getCompositeCMT(lat,lon,depth,dbfile,
                                                               box=minboxcomp,
                                                               depthbox=depthboxcomp,
                                                               maxbox=maxboxcomp,
                                                               dbox=dboxcomp,nmin=nmin)

        dip = config['CONSTANTS']['default_szdip']
        slab_collection = SlabCollection(data_folder,dip)
        slab_params = slab_collection.getSlabInfo(lat,lon)

        reginfo = self._regionalizer.getRegions(lat,lon,depth)
        
        if len(slab_params):
            if np.isnan(slab_params['depth']):
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
                reginfo['FocalMechanism'] = get_focal_mechanism(tensor_params,config)
                results = reginfo.copy()
            else:
                results = self._get_subduction_type(lat,lon,depth,tensor_params,slab_params,reginfo,config)
                results['SlabModelRegion'] = slab_params['region']
                results['SlabModelType'] = slab_params['slabtype']
                results['SlabModelOutside'] = slab_params['outside']
                results['SlabModelDepth'] = slab_params['depth']
                results['SlabModelDip'] = slab_params['dip']
                results['SlabModelStrike'] = slab_params['strike']
        else:
            results = reginfo.copy()
            results['FocalMechanism'] = get_focal_mechanism(tensor_params,config)
            results['SlabModelRegion'] = ''
            results['SlabModelType'] = ''
            results['SlabModelOutside'] = False
            results['SlabModelDepth'] = np.nan
            results['SlabModelDip'] = np.nan
            results['SlabModelStrike'] = np.nan
            results['IsLikeInterface'] = False
            results['IsNearInterface'] = False
            results['IsInSlab'] = False


        results = results.reindex(index=['TectonicRegion','TectonicDomain','FocalMechanism',
                                         'DistanceToStable',
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
        fmstring = get_focal_mechanism(tensor_params,config)
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



def get_focal_mechanism(tensor_params,config):
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
    tplunge_rs = float(config['CONSTANTS']['tplunge_rs'])
    bplunge_ds = float(config['CONSTANTS']['bplunge_ds'])
    bplunge_ss = float(config['CONSTANTS']['bplunge_ss'])
    pplunge_nm = float(config['CONSTANTS']['pplunge_nm'])
    delplunge_ss = float(config['CONSTANTS']['delplunge_ss'])
    if Tp >= tplunge_rs and Np <= bplunge_ds:
        return 'RS'
    if Np >= bplunge_ss and (Tp >= Pp-delplunge_ss and Tp <= Pp+delplunge_ss):
        return 'SS'
    if Pp >= pplunge_nm and Np <= bplunge_ds:
        return 'NM'
    return 'ALL'

