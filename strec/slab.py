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
from obspy.geodetics import gps2dist_azimuth

#local imports
from .proj import geo_to_utm,utm_to_geo

MAX_INTERFACE_DEPTH = 70 #depth beyond which any tectonic regime has to be intraslab

#Slab 1.0 does not have depth uncertainty, so we make this a constant
DEFAULT_DEPTH_ERROR = 10

class GridSlab(object):
    """Represents USGS Slab model grids for a given subduction zone.
    """
    def __init__(self,depth_file,dip_file,strike_file,error_file):
        """Construct GridSlab object from input files.

        Args:
            depth_file (str): Path to Slab depth grid file.
            dip_file (str): Path to Slab dip grid file.
            strike_file (str): Path to Slab strike grid file.
            error_file (str): Path to Slab depth error grid file (can be None).
        """
        self._depth_file = depth_file
        self._dip_file = dip_file
        self._strike_file = strike_file
        self._error_file = error_file #can be None for Slab 1.0

    def contains(self,lat,lon):
        """Check to see if input coordinates are contained inside Slab model.

        Args:
            lat (float):  Hypocentral latitude in decimal degrees.
            lon (float):  Hypocentral longitude in decimal degrees.
        Returns:
            bool: True if point falls inside minimum bounding box of slab model.
        """
        gdict,tmp = GMTGrid.getFileGeoDict(self._depth_file)
        if lat >= gdict.ymin and lat <= gdict.ymax and lon >= gdict.xmin and lon <= gdict.xmax:
            return True
        return False

    def getSlabInfo(self,lat,lon):
        """Return a dictionary with depth,dip,strike, and depth uncertainty.

        Args:
            lat (float):  Hypocentral latitude in decimal degrees.
            lon (float):  Hypocentral longitude in decimal degrees.
        Returns:
            dict: Dictionary containing keys:
                - region Three letter Slab model region code.
                - strike Slab model strike angle.
                - dip Slab model dip angle.
                - depth Slab model depth (km).
                - depth_uncertainty Slab model depth uncertainty.
        """
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
        if self._error_file is not None:
            error_grid = GMTGrid.load(self._error_file)
            error = error_grid.getValue(lat,lon)
        else:
            error = DEFAULT_DEPTH_ERROR
        dip = dip_grid.getValue(lat,lon) * -1
        strike = strike_grid.getValue(lat,lon)
        strike = strike
        if strike < 0:
            strike += 360
        
        slabinfo = {'region':region,
                    'strike':strike,
                    'dip':dip,
                    'depth':depth,
                    'depth_uncertainty':error}
        return slabinfo
    
class SlabCollection(object):
    def __init__(self,datafolder):
        """Object representing a collection of SlabX.Y grids.

        This object can be queried with a latitude/longitude to see if that point is within a subduction
        slab - if so, the slab information is returned.

        Args:
            datafolder (str): String path where grid files and GeoJSON file reside.
        """
        self._depth_files = glob.glob(os.path.join(datafolder,'*_dep*.grd'))
        homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
        
    def getSlabInfo(self,lat,lon,depth):
        """Query the entire set of slab models and return a SlabInfo object, or None.
        
        Args:
            lat (float):  Hypocentral latitude in decimal degrees.
            lon (float):  Hypocentral longitude in decimal degrees.
            depth (float): Hypocentral depth in km.

        Returns:
            dict: Dictionary containing keys:
                - region Three letter Slab model region code.
                - strike Slab model strike angle.
                - dip Slab model dip angle.
                - depth Slab model depth (km).
                - depth_uncertainty Slab model depth uncertainty.
        """

        deep_depth = 99999999999
        slabinfo = {}
        # loop over all slab regions, return keep all slabs found
        for depth_file in self._depth_files:
            dip_file = depth_file.replace('dep','dip')
            strike_file = depth_file.replace('dep','str')
            error_file = depth_file.replace('dep','unc')
            if not os.path.isfile(error_file):
                error_file = None
            gslab = GridSlab(depth_file,dip_file,strike_file,error_file)
            tslabinfo = gslab.getSlabInfo(lat,lon)
            if not len(tslabinfo):
                continue
            else:
                depth = tslabinfo['depth']
                if depth < deep_depth:
                    slabinfo = tslabinfo.copy()
                    deep_depth = depth
            
        return slabinfo
    
