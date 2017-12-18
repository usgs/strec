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
REGIONS['Stable'] = 'stable.json'
REGIONS['Active'] = 'active.json'
REGIONS['Subduction'] = 'subduction.json'
REGIONS['Volcanic'] = 'volcanic.json'

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


def _get_layer_info(layer, point, fname, domain_field=None, default_domain=None):
    """Get information about a given layer with respect to an input point.

    Args:
        layer (str): Name of input layer ("Stable","Active",etc.)
        point (Point): Shapely Point object (lon,lat).
        fname (str): Path to file containing spatial data for layer.
        domain_field (str): Field in fname to find domain (output).
        default_domain (str): If domain_field is None, the domain to output.
    Returns:
        str or None: None if point is not inside layer, name of region if it is.
        float: Distance from point to nearest point on layer.
        domain: Tectonic domain of layer.
        bool: Boolean indicating whether layer has a back-arc subduction region.
    """
    distance_to_layer = 99999999999999999
    shapes = fiona.open(fname, 'r')
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
            dist_to_vertex = _get_nearest_point(point, pshape)
            if dist_to_vertex < distance_to_layer:
                distance_to_layer = dist_to_vertex
    if inside:
        region = layer
        distance = _get_nearest_point(point, pshape)
    else:
        distance = distance_to_layer

    return (region, distance, domain, is_backarc)


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

    def getDomainInfo(self, domain):
        """Get tectonic sub-domain given tectonic domain and depth.

        Args:
            domain (str): SeismoTectonicDomain, one of:
                - SCR (generic)
                - SCR (above slab)
                - ACR (shallow)
                - ACR (deep)
                - ACR (oceanic boundary)
                - ACR (hot spot)
                - SZ (generic)
                - SZ (outer-trench)
                - SZ (on-shore)
                - SZ (inland/back-arc)
                - SOR (generic)
                - SOR (above slab)
                - ACR shallow (above slab)
                - ACR deep (above slab)
                - ACR oceanic boundary (above slab)
        Returns:
            Series: row from domains.xlsx in repository, containing columns:
                - TYPE
                - TectonicDomain
                - H1
                - SubDomain1
                - H2
                - SubDomain2
                - H3
                - SubDomain3
        """
        domainfile = os.path.join(self._datafolder, 'domains.xlsx')
        df = pd.read_excel(domainfile)
        domain_info = df[df.TectonicDomain == domain]
        if not len(domain_info):
            raise KeyError(
                'Could not find domain "%s" in list of domains.' % domain)
        return domain_info.iloc[0]

    def getSubDomain(self, domain, depth):
        """Get tectonic sub-domain given tectonic domain and depth.

        Args:
            domain (str): SeismoTectonicDomain, one of:
                - SCR (generic)
                - SCR (above slab)
                - ACR (shallow)
                - ACR (deep)
                - ACR (oceanic boundary)
                - ACR (hot spot)
                - SZ (generic)
                - SZ (outer-trench)
                - SZ (on-shore)
                - SZ (inland/back-arc)
                - SOR (generic)
                - SOR (above slab)
                - ACR shallow (above slab)
                - ACR deep (above slab)
                - ACR oceanic boundary (above slab)
            depth (float):  Earthquake depth (km).
        Returns:
            str: SeismoTectonicSubDomain, one of: SCR,ACR,SZIntra,Volcanic,SZInter.
            list of tuples of each domain and depth limit.
        """
        domain_info = self.getDomainInfo(domain)

        H1 = domain_info['H1']
        H2 = domain_info['H2']
        H3 = domain_info['H3']

        domain1 = domain_info['SubDomain1']
        domain2 = domain_info['SubDomain2']
        domain3 = domain_info['SubDomain3']

        domain = None

        if depth >= 0 and depth < H1:
            domain = domain1

        if depth >= H1 and depth < H2:
            domain = domain2

        if depth >= H2 and depth < H3:
            domain = domain3

        return (domain, [(domain1, H1), (domain2, H2), (domain3, H3)])

    def getRegions(self, lat, lon, depth):
        """Get information about the tectonic region of a given hypocenter.

        Args:
            lat (float): Earthquake hypocentral latitude.
            lon (float): Earthquake hypocentral longitude.
            depth (float): Earthquake hypocentral depth.
        Returns:
            Series: Pandas series object containing labels:
                - TectonicRegion: Subduction, Active, Stable, or Volcanic.
                - TectonicDomain: One of...
                    - SCR (generic)
                    - SCR (above slab)
                    - ACR (shallow)
                    - ACR (deep)
                    - ACR (oceanic boundary)
                    - ACR (hot spot)
                    - SZ (generic)
                    - SZ (outer-trench)
                    - SZ (on-shore)
                    - SZ (inland/back-arc)
                    - SOR (generic)
                    - SOR (above slab)
                    - ACR shallow (above slab)
                    - ACR deep (above slab)
                    - ACR oceanic boundary (above slab)
                - DistanceToStable: Distance in km to nearest stable region.
                - DistanceToActive: Distance in km to nearest active region.
                - DistanceToSubduction: Distance in km to nearest subduction region.
                - DistanceToVolcanic: Distance in km to nearest volcanic region.
                - Oceanic: Boolean indicating if epicenter is in the ocean.
                - DistanceToOceanic: Distance in km to nearest oceanic region.
                - DistanceToContinental: Distance in km to nearest continental region.
                - TectonicSubDomain: Depth dependent tectonic domain based on simple table.
                - RegionContainsBackArc: Boolean flag indicating whether epicentral region
                                         contains a subduction back-arc.
                - DomainDepthBand1: Depth above which SubDomain1 applies.
                - SubDomain1: Tectonic SubDomain to apply between 0 depth and DomainDepthBand1.
                - DomainDepthBand2: Depth above which (below DomainDepthBand1) where SubDomain2 applies.
                - SubDomain2: Tectonic SubDomain to apply between DomainDeptBand1 and DomainDepthBand2.
                - DomainDepthBand3: Depth above which (below DomainDepthBand2) where SubDomain3 applies.
                - SubDomain3: Tectonic SubDomain to apply between DomainDeptBand2 and DomainDepthBand3.
        """
        regions = OrderedDict()
        point = Point(lon, lat)
        for layer, fname in self._regions.items():
            distance_field = 'DistanceTo%s' % layer
            default_domain = None
            if layer == 'Stable':
                default_domain = 'SCR (generic)'

            region, distance, domain, is_backarc = _get_layer_info(layer, point, fname,
                                                                   domain_field=DOMAIN_FIELD,
                                                                   default_domain=default_domain)

            if region is not None:
                regions['TectonicRegion'] = region
                regions[distance_field] = 0.0
                regions['TectonicDomain'] = domain
                regions['RegionContainsBackArc'] = is_backarc
            else:
                regions[distance_field] = distance

        # Are we oceanic or continental?
        region, distance, domain, tback = _get_layer_info(
            'Oceanic', point, self._oceanic)
        if region is not None:
            regions['Oceanic'] = True
            # figure out how to get distance to edge of containing polygon (shapely says 0)
            regions['DistanceToContinental'] = distance
            regions['DistanceToOceanic'] = 0.0
        else:
            regions['Oceanic'] = False
            regions['DistanceToOceanic'] = distance
            regions['DistanceToContinental'] = 0.0

        subtype, depthinfo = self.getSubDomain(
            regions['TectonicDomain'], depth)
        regions['TectonicSubDomain'] = subtype
        regions['DomainDepthBand1'] = depthinfo[0][1]
        regions['DomainDepthBand1Subtype'] = depthinfo[0][0]
        regions['DomainDepthBand2'] = depthinfo[1][1]
        regions['DomainDepthBand2Subtype'] = depthinfo[1][0]
        regions['DomainDepthBand3'] = depthinfo[2][1]
        regions['DomainDepthBand3Subtype'] = depthinfo[2][0]

        regions = pd.Series(regions, index=['TectonicRegion', 'TectonicDomain', 'DistanceToStable',
                                            'DistanceToActive', 'DistanceToSubduction',
                                            'DistanceToVolcanic', 'Oceanic',
                                            'DistanceToOceanic', 'DistanceToContinental',
                                            'TectonicSubDomain', 'RegionContainsBackArc',
                                            'DomainDepthBand1', 'DomainDepthBand1Subtype',
                                            'DomainDepthBand2', 'DomainDepthBand2Subtype',
                                            'DomainDepthBand3', 'DomainDepthBand3Subtype'])

        return regions
