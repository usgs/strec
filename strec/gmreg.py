#!/usr/bin/env python

# stdlib imports
import glob
import os.path
from collections import OrderedDict
from functools import partial

# third party
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

# local imports
from strec.utils import get_config

# As we add more layers, define their name/file mappings here.
# All of these files have polygons where the attribute is true.
REGIONS = OrderedDict()
REGIONS['Stable'] = 'stable.geojson'
REGIONS['Active'] = 'active.geojson'
REGIONS['Subduction'] = 'subduction.geojson'
REGIONS['Volcanic'] = 'volcanic.geojson'

# for each of the above regions, when we're inside a polygon, we should
# capture the field below as the "Tectonic Domain".
DOMAIN_FIELD = 'REGIME_TYP'
SLABFIELD = 'SLABFLAG'
SCRFIELD = 'SCRFLAG'

# these are special layers (not exclusive with above regions)
# where are the areas of induced seismicity?
INDUCED = 'induced.json'
# where are the areas that are oceanic (i.e., not continental?)
OCEANIC = 'oceanic.json'

# this is a layer with many unassociated polygons that delineate purely geographic areas
# of seismic interest (usually areas which have a specific GMPE).
GEOGRAPHIC = 'geographic.json'

# for each of the above geographic regions, this is the attribute containing the name of the region
GEOGRAPHIC_FIELD = 'REG_NAME'


def _get_nearest_point(point, shape):
    """Return distance from point to nearest vertex of a polygon.

    Args:
        point (Point): Shapely point object (lon,lat).
        shape (shape): Shapely geometry (usually Polygon).

    Returns:
        float: Minimum distance in km from input point to nearest vertex on input shape.
    """
    latlong = pyproj.Proj(
        '+proj=longlat +ellps=WGS84 +datum=WGS84 +units=degrees')
    azim = pyproj.Proj('+proj=aeqd +lat_0=%.6f +lon_0=%.6f' %
                       (point.y, point.x))

    project = partial(
        pyproj.transform,
        latlong,
        azim)

    ppoint = transform(project, point)
    pshape = transform(project, shape)

    if isinstance(pshape, MultiPolygon):
        shapelist = pshape
    else:
        shapelist = [pshape]

    mindist = 99999999999999999999
    for pshape in shapelist:
        pshape_string = LineString(pshape.exterior)
        point_nearest, shape_nearest = nearest_points(ppoint, pshape_string)
        distance = np.sqrt(shape_nearest.x**2 + shape_nearest.y**2) / 1000
        if distance < mindist:
            mindist = distance

    return mindist


def _get_layer_info(layer, point, fname):
    """Get information about a given layer with respect to an input point.

    Args:
        layer (str): Name of input layer ("Stable","Active",etc.)
        point (Point): Shapely Point object (lon,lat).
        fname (str): Path to file containing spatial data for layer.
    Returns:
        str or None: None if point is not inside layer, name of region if it is.
        float: Distance from point to nearest point on layer.
        bool: Boolean indicating whether layer has a back-arc subduction region.
    """
    distance_to_layer = 99999999999999999
    shapes = fiona.open(fname, 'r')
    inside = False
    domain = None
    region = None
    for shape in shapes:
        pshape = tShape(shape['geometry'])
        if pshape.contains(point):
            inside = True
            break
        else:
            dist_to_vertex = _get_nearest_point(point, pshape)
            if dist_to_vertex < distance_to_layer:
                distance_to_layer = dist_to_vertex
    if inside:
        region = layer
        distance = _get_nearest_point(point, pshape)
    else:
        distance = distance_to_layer

    return (region, distance)


class Regionalizer(object):
    def __init__(self, datafolder):
        """Determine tectonic region information given epicenter and depth.

        Args:
            datafolder (str): Path to directory containing spatial data for 
                tectonic regions.
        """
        self._datafolder = datafolder
        self._regions = OrderedDict()
        for layer, fname in REGIONS.items():
            fullfile = os.path.join(datafolder, fname)
            if not os.path.isfile(fullfile):
                raise OSError('File %s not found' % fullfile)
            self._regions[layer] = fullfile
        self._oceanic = os.path.join(datafolder, OCEANIC)
        if not os.path.isfile(self._oceanic):
            raise OSError('File %s not found' % self._oceanic)

    @classmethod
    def load(cls):
        """Load regionalizer data from data in the repository.

        Returns:
            Regionalizer: Instance of Regionalizer class.
        """
        config = get_config()
        datadir = config['DATA']['folder']
        return cls(datadir)

    def getRegions(self, lat, lon, depth):
        """Get information about the tectonic region of a given hypocenter.

        Args:
            lat (float): Earthquake hypocentral latitude.
            lon (float): Earthquake hypocentral longitude.
            depth (float): Earthquake hypocentral depth.
        Returns:
            Series: Pandas series object containing labels:
                - TectonicRegion: Subduction, Active, Stable, or Volcanic.
                - DistanceToStable: Distance in km to nearest stable region.
                - DistanceToActive: Distance in km to nearest active region.
                - DistanceToSubduction: Distance in km to nearest subduction region.
                - DistanceToVolcanic: Distance in km to nearest volcanic region.
                - Oceanic: Boolean indicating if epicenter is in the ocean.
                - DistanceToOceanic: Distance in km to nearest oceanic region.
                - DistanceToContinental: Distance in km to nearest continental region.
        """
        regions = OrderedDict()
        point = Point(lon, lat)
        for layer, fname in self._regions.items():
            distance_field = 'DistanceTo%s' % layer
            default_domain = None
            if layer == 'Stable':
                default_domain = 'SCR (generic)'

            region, distance = _get_layer_info(layer, point, fname)

            if region is not None:
                regions['TectonicRegion'] = region
                regions[distance_field] = 0.0
            else:
                regions[distance_field] = distance

        # Are we oceanic or continental?
        region, distance = _get_layer_info('Oceanic', point, self._oceanic)
        if region is not None:
            regions['Oceanic'] = True
            # figure out how to get distance to edge of containing polygon (shapely says 0)
            regions['DistanceToContinental'] = distance
            regions['DistanceToOceanic'] = 0.0
        else:
            regions['Oceanic'] = False
            regions['DistanceToOceanic'] = distance
            regions['DistanceToContinental'] = 0.0

        regions = pd.Series(regions, index=['TectonicRegion', 'TectonicDomain', 'DistanceToStable',
                                            'DistanceToActive', 'DistanceToSubduction',
                                            'DistanceToVolcanic', 'Oceanic',
                                            'DistanceToOceanic', 'DistanceToContinental'])

        return regions
