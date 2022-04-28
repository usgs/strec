# stdlib imports
from functools import partial

# third party imports
import pyproj
from shapely.ops import transform
import numpy as np


def get_utm_proj(lat, lon):
    """Get the UTM Proj4 projection string best suited for input coordinates.

    Args:
        lat (float): Latitude in decimal degrees.
        lon (float): Longitude in decimal degrees.
    Returns:
        str: Proj4 projection string with appropriate UTM projection.
    """
    hemi = 'north'
    if lat < 0:
        hemi = 'south'
    starts = np.arange(-180, 186, 6)
    zone = np.where((lon > starts) < 1)[0].min()
    projstr = '+proj=utm +zone=%i +%s +ellps=WGS84 +datum=WGS84 +units=m +no_defs' % (
        zone, hemi)
    return projstr


def geo_to_utm(shape, utmstr=None):
    """Project a shapely geometry to UTM.

    Args:
        shape (shapely.geometry.shape): Shapely geometry (Polygon, LineString, etc.)
        utmstr (str): Proj4 projection string with appropriate UTM projection. If None,
            geo_to_utm will select one based on shape centroid.
    Returns:
        shapely.geometry.shape: Input shapely geometry projected to UTM.
        str: Proj4 projection string with UTM projection used.
    """
    if utmstr is None:
        point = shape.centroid
        utmstr = get_utm_proj(point.y, point.x)
    project = partial(
        pyproj.transform,
        pyproj.Proj('+proj=longlat +datum=WGS84'),
        pyproj.Proj(utmstr))

    pshape = transform(project, shape)
    return (pshape, utmstr)


def utm_to_geo(pshape, utmstr):
    """Project a shapely geometry from UTM to geographic coordinates.

    Args:
        shape (shapely.geometry.shape): Shapely geometry (Polygon, LineString, etc.) in
        UTM.
        utmstr (str): Proj4 projection string with appropriate UTM projection.
    Returns:
        shapely.geometry.shape: Input shapely geometry projected to UTM.
    """
    reverse = partial(
        pyproj.transform,
        pyproj.Proj(utmstr),
        pyproj.Proj('+proj=longlat +datum=WGS84'),)
    shape = transform(reverse, pshape)
    return shape
