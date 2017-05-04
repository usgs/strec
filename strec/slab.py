#stdlib imports
import os.path
import json
import glob
from functools import partial

#third party imports
from mapio.gmt import GMTGrid
import numpy as np
import fiona
from shapely.ops import transform
from shapely.geometry import shape as tshape
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon
from openquake.hazardlib.geo.geodetic import geodetic_distance,azimuth

#local imports
from .proj import geo_to_utm,utm_to_geo

DEFAULT_SZ_DIP = 17.0 #default dip angle of subduction zone
MAX_INTERFACE_DEPTH = 70 #depth beyond which any tectonic regime has to be intraslab

class SlabInfo(object):
    def __init__(self,strike,dip,depth,region,slabtype,outside):
        """Container object for slab information.

        :param strike:
          Strike angle of the interface.
        :param dip:
          Dip angle of the interface.
        :param depth:
          Depth to slab at a given input latitude/longitude.
        :param region:
          Name of slab or trench from which slab info was derived.
        :param slabtype:
          'grid' (USGS gridded Slab model) or 'trench' (line of strike angles and assumed constant dip).
        :param outside:
          Boolean indicating whether the input coordinate is on the dipping side of the interface line.
        """
        self._strike = strike
        self._dip = dip
        self._depth = depth
        self._region = region
        self._slabtype = slabtype
        self._outside = outside

    @property
    def strike(self):
        return self._strike

    @property
    def dip(self):
        return self._dip

    @property
    def depth(self):
        return self._depth

    @property
    def region(self):
        return self._region

    @property
    def slabtype(self):
        return self._slabtype

    @property
    def outside(self):
        return self._outside

class Slab(object):
    def contains(self,lat,lon):
        pass

    def getSlabInfo(self,lat,lon):
        pass

class GridSlab(Slab):
    def __init__(self,depth_file,dip_file,strike_file):
        self._depth_file = depth_file
        self._dip_file = dip_file
        self._strike_file = strike_file

    def contains(self,lat,lon):
        gdict,tmp = GMTGrid.getFileGeoDict(self._depth_file)
        if lat >= gdict.ymin and lat <= gdict.ymax and lon >= gdict.xmin and lon <= gdict.xmax:
            return True
        return False

    def getSlabInfo(self,lat,lon):
        slabinfo = {}
        if not self.contains(lat,lon):
            return slabinfo
        fpath,fname = os.path.split(self._depth_file)
        parts = fname.split('_')
        region = parts[0]
        depth_grid = GMTGrid.load(self._depth_file)
        depth = -1 * depth_grid.getValue(lat,lon) #slab grids are negative depth
        dip_grid = GMTGrid.load(self._dip_file)
        strike_grid = GMTGrid.load(self._strike_file)
        dip = dip_grid.getValue(lat,lon) * -1
        strike = strike_grid.getValue(lat,lon)
        strike = strike - 90
        if strike < 0:
            strike += 360
        slabinfo = {'region':region,
                    'strike':strike,
                    'dip':dip,
                    'depth':depth,
                    'outside':np.isnan(depth),
                    'slabtype':'grid'}
        return slabinfo

class TrenchSlab(Slab):
    def __init__(self,trenchfile,dip=DEFAULT_SZ_DIP):
        jdict = json.load(open(trenchfile,'rt'))
        self._shape = tshape(jdict['geometry'])
        self._strike = jdict['properties']['strike']
        self._dip = dip
        self._region = jdict['properties']['name']

    def _getUTMProj(self,lat,lon):
        hemi = 'north'
        if lat < 0:
            hemi='south'
        starts = np.arange(-180,180,6)
        zone = np.where((lon > starts) < 1)[0].min()
        projstr = '+proj=utm +zone=%i +%s +ellps=WGS84 +datum=WGS84 +units=m +no_defs' % (zone,hemi)
        return projstr
        
    def contains(self,lat,lon):
        shape = self._shape
        xmin,ymin,xmax,ymax = shape.bounds
            
        rect = Polygon([(xmin,ymin),(xmin,ymax),(xmax,ymax),(xmax,ymin),(xmin,ymin)])
        if rect.contains(Point(lon,lat)):
            return True

        #now we need to look landward 21 km from interface to see if we're inside that polygon
        #let's use shapely to buffer the feature outwards in all directions the required distance
        #first we'll need to project this feature to UTM
        pshape,utmstr = geo_to_utm(shape)
        #set the buffer distance based on the maximum depth for an interface EVER       
        buffer_distance = MAX_INTERFACE_DEPTH / np.tan(np.radians(self._dip))
        pshape_buffer = pshape.buffer(buffer_distance)
        shape_buffer = utm_to_geo(pshape_buffer,utmstr)
        if shape_buffer.contains(Point(lon,lat)):
            return True
        return False

    def getSlabInfo(self,lat,lon):
        slabinfo = {}
        if not self.contains(lat,lon):
            return slabinfo
        mindist = 9999999999
        minlat = 999
        minlon = 999
        minstrike = 999
        for i in range(0,len(self._shape.coords)):
            slon,slat = self._shape.coords[i]
            strike = self._strike[i]
            dist = geodetic_distance(lat,lon,slat,slon)
            if dist < mindist:
                mindist = dist
                minlat = slat
                minlon = slon
                minstrike = strike
        lineaz = azimuth(minlat,minlon,lat,lon)
        dstrike = minstrike - lineaz
        region = self._region
        depth = mindist * np.tan(np.radians(self._dip))
        if dstrike >= 360:
            dstrike = dstrike - 360
        if dstrike < 0:
            dstrike = dstrike + 360
        if dstrike > 0 and dstrike < 180:
            outside = True
        else:
            outside = False
        slabinfo = {'region':region,
                    'strike':minstrike,
                    'dip':self._dip,
                    'depth':depth,
                    'outside':outside,
                    'slabtype':'trench'}
        return slabinfo
    
class SlabCollection(object):
    def __init__(self,datafolder,default_sz_dip=DEFAULT_SZ_DIP):
        """Object representing a collection of SlabX.Y grids and a trench file in GeoJSON format.

        This object can be queried with a latitude/longitude to see if that point is within a subduction
        slab - if so, the slab information is returned.

        :param datafolder:
          String path where grid files and GeoJSON file reside.
        :param default_sz_dip:
          Default value of dip for slabs represented as trench lines.
        """
        self._depth_files = glob.glob(os.path.join(datafolder,'*_clip.grd'))
        self._trench_files = glob.glob(os.path.join(datafolder,'*.json'))
        self._default_sz_zip = default_sz_dip
        
    def getSlabInfo(self,lat,lon):
        """Query the entire set of slab models and return a SlabInfo object, or None.

        :param lat:
          Input latitude.
        :param lon:
          Input longitude.
        :returns:
          A SlabInfo object, in the cases where:
            1) The coordinate is inside a slab grid, landward of the interface.
            2) The coordinate is inside a slab grid, oceanward of the interface.
            3) The coordinate is inside (??) a trench line, landward of the interface.
            4) The coordinate is inside (??) a trench line, oceanward of the interface.

            When the coordinate is not dip-ward of the interface, SlabInfo properties will be set to NaN.
        None, when the coordinate is not inside any of the slab grids or the trenches.
        """
        
        slabinfo = {}
        for depth_file in self._depth_files:
            dip_file = depth_file.replace('clip','dipclip')
            strike_file = depth_file.replace('clip','strclip')
            gslab = GridSlab(depth_file,dip_file,strike_file)
            slabinfo = gslab.getSlabInfo(lat,lon)
            if not len(slabinfo):
                continue
            else:
                return slabinfo

        if not len(slabinfo):
            for trench_file in self._trench_files:
                tslab = TrenchSlab(trench_file)
                slabinfo = tslab.getSlabInfo(lat,lon)
                if not len(slabinfo):
                    continue
                else:
                    return slabinfo
        

        return slabinfo
    
