#!/usr/bin/env python

#stdlib imports
import glob
import os.path
from collections import OrderedDict
from functools import partial

#third party
import fiona
from shapely.geometry import shape as tShape
from shapely.geometry.point import Point
from shapely.geometry.linestring import LineString
from shapely.geometry.multipolygon import MultiPolygon
from shapely.ops import nearest_points
from shapely.ops import transform
import pyproj
import numpy as np
from obspy.geodetics.base import gps2dist_azimuth
import pandas as pd

#As we add more layers, define their name/file mappings here.
#All of these files have polygons where the attribute is true.
REGIONS = OrderedDict()
REGIONS['Stable'] = 'stable.json'
REGIONS['Active'] = 'active.json'
REGIONS['Subduction'] = 'subduction.json'
REGIONS['Volcanic'] = 'volcanic.json'

#for each of the above regions, when we're inside a polygon, we should
#capture the field below as the "Tectonic Domain".
DOMAIN_FIELD = 'REGIME_TYP'
SLABFIELD = 'SLABFLAG'
SCRFIELD = 'SCRFLAG'

#these are special layers (not exclusive with above regions)
#where are the areas of induced seismicity?
INDUCED = 'induced.json'
#where are the areas that are oceanic (i.e., not continental?)
OCEANIC = 'oceanic.json'

#this is a layer with many unassociated polygons that delineate purely geographic areas
#of seismic interest (usually areas which have a specific GMPE).
GEOGRAPHIC = 'geographic.json'

#for each of the above geographic regions, this is the attribute containing the name of the region
GEOGRAPHIC_FIELD = 'REG_NAME'

def _get_nearest_point(point,shape,inside=False):
    """Return distance from point to nearest vertex of a polygon.

    
    """
    latlong = pyproj.Proj('+proj=longlat +ellps=WGS84 +datum=WGS84 +units=degrees')
    azim = pyproj.Proj('+proj=aeqd +lat_0=%.6f +lon_0=%.6f' % (point.y,point.x))
    
    project = partial(
    pyproj.transform,
    latlong,
    azim)

    ppoint = transform(project, point)
    pshape = transform(project, shape)

    if isinstance(pshape,MultiPolygon):
        shapelist = pshape
    else:
        shapelist = [pshape]

    mindist = 99999999999999999999
    for pshape in shapelist:
        pshape_string = LineString(pshape.exterior)
        point_nearest,shape_nearest = nearest_points(ppoint,pshape_string)
        distance = np.sqrt(shape_nearest.x**2 + shape_nearest.y**2)/1000
        if distance < mindist:
            mindist = distance

    return mindist
        
def _get_layer_info(layer,point,fname,domain_field=None,default_domain=None):
    distance_to_layer = 99999999999999999
    shapes = fiona.open(fname,'r')
    inside = False
    domain = None
    region = None
    is_backarc = False
    for shape in shapes:
        pshape = tShape(shape['geometry'])
        if pshape.contains(point):
            inside = True
            if domain_field is not None:
                domain = shape['properties'][DOMAIN_FIELD]
                if domain is None:
                    domain = default_domain
                    
                if SLABFIELD in shape['properties']:
                    is_backarc = shape['properties'][SLABFIELD] == 'a'
            break
        else:
            dist_to_vertex = _get_nearest_point(point,pshape)
            if dist_to_vertex < distance_to_layer:
                distance_to_layer = dist_to_vertex
    if inside:
        region = layer
        distance = _get_nearest_point(point,pshape,inside=True)
    else:
        distance = distance_to_layer

    return (region,distance,domain,is_backarc)

class Regionalizer(object):
    def __init__(self,datafolder):
        """Determine tectonic region information given epicenter and depth.
        """
        self._datafolder = datafolder
        self._regions = OrderedDict()
        for layer,fname in REGIONS.items():
            fullfile = os.path.join(datafolder,fname)
            if not os.path.isfile(fullfile):
                raise OSError('File %s not found' % fullfile)
            self._regions[layer] = fullfile
        self._oceanic = os.path.join(datafolder,OCEANIC)
        if not os.path.isfile(self._oceanic):
            raise OSError('File %s not found' % self._oceanic)

    @classmethod
    def load(cls):
        """Load regionalizer data from data in the repository.
        
        """
        homedir = os.path.dirname(os.path.abspath(__file__))
        datadir = os.path.join(homedir,'data')
        return cls(datadir)

    def getDomainInfo(self,domain):
        """Return domain information from repository spreadsheet.
        
        :param domain:
          Seismo-tectonic domain ("SZ (generic)",
        """
        regimefile = os.path.join(self._datafolder,'regimes.xlsx')
        df = pd.read_excel(regimefile)
        try:
            reginfo = df[df.REGIME_TYPE == domain].iloc[0]
        except:
            raise Exception('Could not find domain "%s" in list of domains.' % domain)
        return reginfo
        
    
    def getSubType(self,domain,depth):
        """Get 

        """
        reginfo = self.getDomainInfo(domain)
        
        H1 = reginfo['H1']
        H2 = reginfo['H2']
        H3 = reginfo['H3']
        
        reg1 = reginfo['REGIME1']
        reg2 = reginfo['REGIME2']
        reg3 = reginfo['REGIME3']

        regime = None
        
        if depth >= 0 and depth < H1:
            regime = reg1

        if depth >= H1 and depth < H2:
            regime = reg2

        if depth >= H2 and depth < H3:
            regime = reg3

        return (regime,[(reg1,H1),(reg2,H2),(reg3,H3)])
            
     
    def getRegions(self,lat,lon,depth):
        regions = OrderedDict()
        point = Point(lon,lat)
        for layer,fname in self._regions.items():
            distance_field = 'DistanceTo%s' % layer
            default_domain = None
            if layer == 'Stable':
                default_domain = 'SCR (generic)'
                
            region,distance,domain,is_backarc = _get_layer_info(layer,point,fname,
                                                                domain_field=DOMAIN_FIELD,
                                                                default_domain=default_domain)
            
            if region is not None:
                regions['TectonicRegion'] = region
                regions[distance_field] = 0.0
                regions['TectonicDomain'] = domain
                regions['RegionContainsBackArc'] = is_backarc
            else:
                regions[distance_field] = distance

        #Are we oceanic or continental?
        region,distance,domain,tback = _get_layer_info('Oceanic',point,self._oceanic)
        if region is not None:
            regions['Oceanic'] = True
            #figure out how to get distance to edge of containing polygon (shapely says 0)
            regions['DistanceToContinental'] = distance
            regions['DistanceToOceanic'] = 0.0
        else:
            regions['Oceanic'] = False
            regions['DistanceToOceanic'] = distance
            regions['DistanceToContinental'] = 0.0

        subtype,depthinfo = self.getSubType(regions['TectonicDomain'],depth)
        regions['TectonicSubtype'] = subtype
        regions['DomainDepthBand1'] = depthinfo[0][1]
        regions['DomainDepthBand1Subtype'] = depthinfo[0][0]
        regions['DomainDepthBand2'] = depthinfo[1][1]
        regions['DomainDepthBand2Subtype'] = depthinfo[1][0]
        regions['DomainDepthBand3'] = depthinfo[2][1]
        regions['DomainDepthBand3Subtype'] = depthinfo[2][0]

        regions = pd.Series(regions,index=['TectonicRegion','TectonicDomain','DistanceToStable',
                                         'DistanceToActive','DistanceToSubduction',
                                         'DistanceToVolcanic','Oceanic',
                                         'DistanceToOceanic','DistanceToContinental',
                                         'TectonicSubtype','RegionContainsBackArc',
                                         'DomainDepthBand1','DomainDepthBand1Subtype',
                                         'DomainDepthBand2','DomainDepthBand2Subtype',
                                         'DomainDepthBand3','DomainDepthBand3Subtype'])
        
        
        # #Are we induced or tectonic?
        # region,distance,domain = _get_layer_info('Induced',point,self._induced)
        # if region is not None:
        #     regions['Induced'] = True
        #     #figure out how to get distance to edge of containing polygon (shapely says 0)
        #     regions['DistanceToTectonic'] = None 
        # else:
        #     regions['Induced'] = False
        #     regions['DistanceToInduced'] = distance
            

        # #what geographic regions are we in?
        # geoshapes = fiona.open(self._geographic)
        # geographic_regions = []
        # for shape in geoshapes:
        #     pshape = tShape(shape['geometry'])
        #     if pshape.contains(point):
        #         geographic_regions.append(shape['properties'][GEOGRAPHIC_FIELD])
        # regions['GeographicRegions'] = ','.join(geographic_regions)
        return regions
        

