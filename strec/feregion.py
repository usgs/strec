#!/usr/bin/env python

#stdlib imports
import os.path

#third party imports
import fiona
from shapely.geometry import shape as tshape
from shapely.geometry.point import Point
import pandas as pd

#local imports
from .subduction import SubductionZone
from .slab import SlabCollection
from .cmt import getCompositeCMT
from .proj import geo_to_utm

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

    
        
    def getRegion(self,lat,lon,depth,magnitude):
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

    def getRegimeInfo(self,lat,lon,depth,magnitude,config,tensor_params=None):
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
        regime,regime_warning = self.getRegime(lat,lon,depth,magnitude,
                                               tensor_params,slab_params,config)
        return (regime,regime_warning)

    def modify_reginfo(self,reginfo,regtype=None):
        if regtype is None:
            regtype = reginfo['REGIME_TYPE']
        #get the depth/regime info for this type
        df_regimes = pd.read_excel(self._fecodes,index_col=None,sheetname='regimes')
        row = df_regimes[df_regimes.TYPE == regtype].iloc[0]

        reginfo.update(row.to_dict())
        return reginfo

    def _get_regime_by_depth(self,reginfo):
        if depth >= 0 and depth < reginfo['H1']:
            regime = reginfo['REGIME1']
            warning = ''
        elif depth >= reginfo['H1'] and depth < reginfo['H2']:
            regime = reginfo['REGIME2']
            warning = ''
        elif depth >= reginfo['H2'] and depth < reginfo['H3']:
            regime = reginfo['REGIME3']
            warning = ''
        else:
            regime = reginfo['REGIME_WARNING']
            warning = ''
        reginfo['regime'] = regime
        return reginfo
    
    def getRegime(self,lat,lon,depth,magnitude,tensor_params,slab_params,config):
        scr_dist = config['constants']['scr_dist']
        reginfo = self.getRegion(lat,lon,depth,magnitude)
        warning = ''
        if reginfo['SCRFLAG']:
            in_stable,region_name,region_code,mindist = inside_stable_region(lat,lon)
            #if we're technically in a stable region, but really close to the edge, then
            #not really in the stable region
            if in_stable:
                if mindist < scr_dist:
                    in_stable = False
                    distwarning = 'WARNING: Event is less than %.1f kilometers from the edge of a stable polygon' % scr_dist
            if in_stable:
                if reginfo['scrflag']:
                    reginfo = self.modify_reginfo(reginfo,'SCR (generic)')
                    reginfo['regime'] = self._get_regime_by_depth(reginfo)
                else:
                    reginfo = self.modify_reginfo(reginfo,'SCR (above slab)')
                    reginfo['regime'] = self._get_regime_by_depth(reginfo)
            return reginfo
        
        if not reginfo['REGIME_TYPE'].startswith('SZ'): #not subduction zone
            reginfo = self.modify_reginfo(reginfo)
            return reginfo
        else: #we are in a subduction zone
            if reginfo['REGIME_TYPE'] == 'SZ (generic)':
                if slab_params['outside']:
                    reginfo = self.modify_reginfo(reginfo,'SZ (outer-trench)')
                else:
                    if np.isnan(slab_params['depth']): #although in a SZ, not inside the slab we have.
                        if reginfo['SLABFLAG'] == 'a': #there is a back-arc region inside this FE
                            reginfo = self.modify_reginfo(reginfo,'SZ (inland/back-arc)')
                        else: #no backarc present, do normal subduction zone stuff
                            pass
                if depth <= reginfo['H1']:
                    depthzone =  "shallow"
                elif depth > reginfo['H1'] and depth <= reginfo['H2']:
                    depthzone = "medium"
                else:
                    depthzone = "deep"
                reginfo,warning = self.getSubductionRegime(lat,lon,depth,magnitude,
                                                  tensor_params,slab_params,
                                                  reginfo,depthzone,config)
        return (reginfo,warning)

    def getSubductionRegime(self,lat,lon,depth,magnitude,
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
                        regime = 'SZinter'
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
                if fmstring == 'ALL' and plungevals is None:
                    if is_near_interface:
                        regime = 'SZinter'
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
                        regime = 'SZinter'
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
                if fmstring == 'ALL' and plungevals is None:
                    if is_near_interface:
                        regime = 'SZinter'
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

        reginfo['regime'] = regime
        return reginfo,warning
