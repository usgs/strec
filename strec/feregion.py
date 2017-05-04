#!/usr/bin/env python

#stdlib imports
import os.path
from collections import OrderedDict

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

def compile_results(reginfo,lat,lon,depth,
                    tensor_params,slab_params,fmstring,regime_warning,distance_warning,
                    interface_dict):
    d = OrderedDict()
    d['Lat'] = lat
    d['Lon'] = lon
    d['Depth'] = depth
    d['SourceRegime'] = reginfo['regime']
    d['TectonicDomain'] = reginfo['REGIME_TYPE']
    d['FocalMechanismType'] = fmstring
    d['FERegionName'] = reginfo['NAME']
    d['FERegionNumber'] = reginfo['FEGR']

    #fill in moment tensor stuff
    if tensor_params is not None:
        tstrike,tplunge = (tensor_params['T']['azimuth'],tensor_params['T']['plunge'])
        pstrike,pplunge = (tensor_params['P']['azimuth'],tensor_params['P']['plunge'])
        nstrike,nplunge = (tensor_params['N']['azimuth'],tensor_params['N']['plunge'])
        fmech = OrderedDict()
        taxis = OrderedDict([('Strike',tstrike),('Plunge',tplunge)])
        paxis = OrderedDict([('Strike',pstrike),('Plunge',pplunge)])
        naxis = OrderedDict([('Strike',nstrike),('Plunge',nplunge)])
        fmech['TAxis'] = taxis
        fmech['PAxis'] = paxis
        fmech['NAxis'] = naxis
    else:
        fmech = OrderedDict()
        taxis = OrderedDict([('Strike',np.nan),('Plunge',np.nan)])
        paxis = OrderedDict([('Strike',np.nan),('Plunge',np.nan)])
        naxis = OrderedDict([('Strike',np.nan),('Plunge',np.nan)])
        fmech['TAxis'] = taxis
        fmech['PAxis'] = paxis
        fmech['NAxis'] = naxis

    d['FocalMechanismParameters'] = fmech
    #slab info
    if not len(slab_params):
        d['SlabParameters'] = OrderedDict([('Strike',np.nan),
                                           ('Dip',np.nan),
                                           ('Depth',np.nan),
                                           ('Outside',False),
                                           ('Source','NA')])
    else:
        slabstrike = slab_params['strike']
        slabdip = slab_params['dip']
        slabdepth = slab_params['depth']
        slaboutside = slab_params['outside']
        slabsource = slab_params['slabtype']
        d['SlabParameters'] = OrderedDict([('Strike',slabstrike),
                                           ('Dip',slabdip),
                                           ('Depth',slabdepth),
                                           ('Outside',slaboutside),
                                           ('Source',slabsource)])
    
    d['IsInterfaceLike'] = interface_dict['is_interface_like']
    d['WithinInterfaceDepthInterval'] = interface_dict['is_near_interface']
    d['WithinIntraslabDepthInterval'] = interface_dict['is_in_slab']
    d['Warning'] = regime_warning + distance_warning

    return d
    

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
    tplunge_rs = config['constants']['tplunge_rs']
    bplunge_ds = config['constants']['bplunge_ds']
    bplunge_ss = config['constants']['bplunge_ss']
    pplunge_nm = config['constants']['pplunge_nm']
    delplunge_ss = config['constants']['delplunge_ss']
    if Tp >= tplunge_rs and Np <= bplunge_ds:
        return 'RS'
    if Np >= bplunge_ss and (Tp >= Pp-delplunge_ss and Tp <= Pp+delplunge_ss):
        return 'SS'
    if Pp >= pplunge_nm and Np <= bplunge_ds:
        return 'NM'
    return 'ALL'

def inside_stable_region(lat,lon):
    #project these polygons and the point to utm so we can get distance in km
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    datadir = os.path.abspath(os.path.join(homedir,'data'))
    polyfile = os.path.join(datadir,'stable_polygons.json')
    polygons = fiona.open(polyfile,'r')
    region_name = None
    region_code = None
    inside = False
    mindist = None
    for polygon in polygons:
        shape = tshape(polygon['geometry'])
        pshape,utmstr = geo_to_utm(shape)
        ppoint,utmstr = geo_to_utm(Point(lon,lat),utmstr=utmstr)

        if pshape.contains(ppoint):
            poly_points = pshape.exterior.coords[:]
            mindist = 9999999999999999999999999999
            for poly_point in poly_points:
                pd = ppoint.distance(Point(poly_point))/1000
                if pd < mindist:
                    mindist = pd
            inside = True
            region_name = polygon['properties']['regionname']
            region_code = polygon['properties']['regioncode']
            break
    polygons.close()

    return (inside,region_name,region_code,mindist)

class FERegions(object):
    def __init__(self):
        homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
        datadir = os.path.abspath(os.path.join(homedir,'data'))
        self._fecodes = os.path.join(datadir,'fecodes.xlsx')
        self._fepolygons = os.path.join(datadir,'fepolygons.json')
        self._fesplits = os.path.join(datadir,'fesplits.json')
        self._stable_polygons = os.path.join(datadir,'fesplits.json')

    
        
    def getRegion(self,lat,lon,depth):
        polygons = fiona.open(self._fepolygons,'r')
        regioncode = None
        for polygon in polygons:
            shape = tshape(polygon['geometry'])
            regioncode = polygon['properties']['regioncode']
            if shape.contains(Point(lon,lat)):
                break
        polygons.close()
        if regioncode is None:
            raise Exception('No Flinn-Engdahl region found for lat/lon %.4f,%.4f.' % (lat,lon))
        
        df = pd.read_excel(self._fecodes,index_col=None,sheetname='fecodes')
        row = df[df.FEGR == regioncode].iloc[0]

        if int(row['SPLITFLAG']):
            splits = fiona.open(self._fesplits,'r')
            for splitpoly in splits:
                shape = tshape(splitpoly['geometry'])
                if shape.contains(Point(lon,lat)):
                    row['TYPE'] = splitpoly['properties']['regime']
                    break
            splits.close

        rowdict = row.to_dict()

        #get the depth/regime info for this type
        df_regimes = pd.read_excel(self._fecodes,index_col=None,sheetname='regimes')
        row = df_regimes[df_regimes.TYPE == rowdict['TYPE']].iloc[0]

        rowdict.update(row.to_dict())
        
        return rowdict

    def getRegimeInfo(self,lat,lon,depth,config,tensor_params=None):
        data_folder = config['data']['folder']
        dip = config['constants']['default_szdip']
        slab_collection = SlabCollection(data_folder,dip)
        slab_params = slab_collection.getSlabInfo(lat,lon)
        if tensor_params is None:
            dbfile = os.path.join(data_folder,'gcmt.db')
            minboxcomp = config['constants']['minradial_distcomp']
            maxboxcomp = config['constants']['maxradial_distcomp']
            dboxcomp = config['constants']['step_distcomp']
            depthboxcomp = config['constants']['depth_rangecomp']

            #Minimum number of events required to get composite mechanism
            nmin = config['constants']['minno_comp']
            tensor_params,tensor_warning = getCompositeCMT(lat,lon,depth,dbfile,
                                                           box=minboxcomp,
                                                           depthbox=depthboxcomp,
                                                           maxbox=maxboxcomp,
                                                           dbox=dboxcomp,nmin=nmin)
        results = self.getRegime(lat,lon,depth,tensor_params,slab_params,config)
        return results

    def modify_reginfo(self,reginfo,regtype=None):
        if regtype is None:
            regtype = reginfo['TYPE']
        #get the depth/regime info for this type
        df_regimes = pd.read_excel(self._fecodes,index_col=None,sheetname='regimes')
        row = df_regimes[df_regimes.TYPE == regtype].iloc[0]

        reginfo.update(row.to_dict())
        return reginfo

    def getRegime(self,lat,lon,depth,tensor_params,slab_params,config):
        scr_dist = config['constants']['scr_dist']
        reginfo = self.getRegion(lat,lon,depth)
        regime_warning = ''
        distance_warning = ''
        interface_dict = {'is_interface_like':False,
                          'is_near_interface':False,
                          'is_in_slab':False}
        if reginfo['SCRFLAG']:
            in_stable,region_name,region_code,mindist = inside_stable_region(lat,lon)
            #if we're technically in a stable region, but really close to the edge, then
            #not really in the stable region
            if in_stable:
                if mindist < scr_dist:
                    in_stable = False
                    distance_warning = 'WARNING: Event is less than %.1f kilometers from the edge of a stable polygon' % scr_dist
            if in_stable:
                if reginfo['scrflag']:
                    reginfo = self.modify_reginfo(reginfo,'SCR (generic)')
                    reginfo['regime'],regime_warning = self.getNonSubdictionRegime(reginfo,depth)
                else:
                    reginfo = self.modify_reginfo(reginfo,'SCR (above slab)')
                    reginfo['regime'],regime_warning = self.getNonSubdictionRegime(reginfo,depth)
            

        #don't have to check the split flag, as that's already taken care of in getRegion
        else:
            if not reginfo['REGIME_TYPE'].startswith('SZ'): #not subduction zone
                reginfo = self.modify_reginfo(reginfo)
                reginfo['regime'],regime_warning = self.getNonSubdictionRegime(reginfo,depth)
            else: #we are in a subduction zone
                if depth <= reginfo['H1']:
                    depthzone =  "shallow"
                elif depth > reginfo['H1'] and depth <= reginfo['H2']:
                    depthzone = "medium"
                else:
                    depthzone = "deep"
                if reginfo['REGIME_TYPE'] == 'SZ (generic)':
                    if 'outside' in slab_params and slab_params['outside']:
                        reginfo = self.modify_reginfo(reginfo,'SZ (outer-trench)')
                        reginfo['regime'],regime_warning,interface_dict = self.getNonSubdictionRegime(reginfo,depth)
                    else:
                        if not len(slab_params) or np.isnan(slab_params['depth']): #although in a SZ, not inside the slab we have.
                            if reginfo['SLABFLAG'] == 'a': #there is a back-arc region inside this FE
                                reginfo = self.modify_reginfo(reginfo,34)
                                reginfo['regime'],regime_warning = self.getNonSubdictionRegime(reginfo,depth)
                            else: #no backarc present, do normal subduction zone stuff
                                reginfo['regime'],regime_warning,interface_dict = self.getSubductionRegime(lat,lon,depth,
                                                                                            tensor_params,slab_params,
                                                                                            reginfo,depthzone,config)
                        else: #inside the subduction zone, check it...
                            reginfo['regime'],regime_warning,interface_dict = self.getSubductionRegime(lat,lon,depth,
                                                                                        tensor_params,slab_params,
                                                                                        reginfo,depthzone,config)

                elif reginfo['REGIME_TYPE'] == 'SZ (on-shore)':
                    if reginfo['SLABFLAG'] == 'a': #there is a back-arc region inside this FE
                        reginfo = self.modify_reginfo(reginfo,34)
                        reginfo['regime'],regime_warning = self.getNonSubdictionRegime(reginfo,depth)
                    else: #no backarc present, do normal subduction zone stuff
                        reginfo['regime'],regime_warning,interface_dict = self.getSubductionRegime(lat,lon,depth,
                                                                                    tensor_params,slab_params,
                                                                                    reginfo,depthzone,config)
                else: #these other "subduction zone" domains aren't really subduction zones
                    reginfo['regime'],regime_warning = self.getNonSubdictionRegime(reginfo,depth)
        fmstring = get_focal_mechanism(tensor_params,config)
        results = compile_results(reginfo,lat,lon,depth,
                                      tensor_params,slab_params,
                                      fmstring,regime_warning,distance_warning,
                                      interface_dict)
        return results

    def getNonSubdictionRegime(self,reginfo,depth):
        H1 = reginfo['H1']
        H2 = reginfo['H2']
        H3 = reginfo['H3']

        #we need to check the depths to see which ones are valid
        h2_depth_valid = True
        h3_depth_valid = True
        if H2 == '-':
            h2_depth_valid = False
        if H3 == '-':
            h3_depth_valid = False
        
        reg1 = reginfo['REGIME1']
        reg2 = reginfo['REGIME2']
        reg3 = reginfo['REGIME3']
        regwarn = reginfo['REGIME_WARNING']
        if depth >= 0 and depth < H1:
            return (reg1,'')
        if h2_depth_valid:
            if depth >= reginfo['H1'] and depth < reginfo['H2']:
                return (reginfo['REGIME2'],'')

        if h2_depth_valid and h3_depth_valid:
            if depth >= reginfo['H1'] and depth < reginfo['H2']:
                return (reginfo['REGIME3'],'')
        else:
            if regwarn != '-':
                return (regwarn,'WARNING')
        return (None,'WARNING')

    def getSubductionRegime(self,lat,lon,depth,
                            tensor_params,slab_params,reginfo,
                            depthzone,config):
        fmstring = get_focal_mechanism(tensor_params,config)
        szinfo = SubductionZone(slab_params,tensor_params,depth,config)
        is_interface_like = szinfo.checkRupturePlane()
        is_near_interface = szinfo.checkInterfaceDepth()
        is_in_slab = szinfo.checkSlabDepth(reginfo['H1'])

        #get the bottom of the active crustal shallowest depth zone
        df_regimes = pd.read_excel(self._fecodes,index_col=None,sheetname='regimes')
        row = df_regimes[df_regimes.REGIME_TYPE == 'ACR (shallow)'].iloc[0]
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
                            regime = 'ACRsh'
                            warning = 'Event near/below interface'
                        else:
                            regime = 'ACRsh'
                else:
                    if is_in_slab:
                        regime = 'ACRsh'
                        warning = 'Event near/below interface'
                    else:
                        regime = 'ACRsh'
            else: #fmstring is 'SS' or 'NM' or 'ALL'
                if fmstring == 'ALL' and tensor_params is None:
                    if is_near_interface:
                        regime = 'SZInter'
                        warning = 'No focal mechanism available'
                    else:
                        if is_in_slab:
                            regime = 'ACRsh'
                            warning = 'Event near/below interface'
                        else:
                            regime = 'ACRsh'
                else:
                    if is_in_slab:
                        regime = 'ACRsh'
                        warning = 'Event near/below interface'
                    else:
                        regime = 'ACRsh'
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
                                regime = 'ACRde'
                            else:
                                regime = 'ACRsh'
                else:
                    if is_in_slab:
                        regime = 'SZIntra'
                    else:
                        if depth > acr_depth:
                            regime = 'ACRde'
                        else:
                            regime = 'ACRsh'
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
                                regime = 'ACRde'
                            else:
                                regime = 'ACRsh'
                else:
                    if is_in_slab:
                        regime = 'SZIntra'
                    else:
                        if depth > acr_depth:
                            regime = 'ACRde'
                        else:
                            regime = 'ACRsh'
        elif depthzone == 'deep':
            if is_in_slab:
                regime = 'SZIntra'
            else:
                warning = 'Event above interface'
                regime = 'SZIntra'

        interface_dict = {'is_interface_like':is_interface_like,
                          'is_near_interface':is_near_interface,
                          'is_in_slab':is_in_slab}
        return (regime,warning,interface_dict)
