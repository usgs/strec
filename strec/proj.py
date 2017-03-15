#stdlib imports
from functools import partial

#third party imports
import pyproj
from shapely.ops import transform
import numpy as np

def get_utm_proj(lat,lon):
    hemi = 'north'
    if lat < 0:
        hemi='south'
    starts = np.arange(-180,180,6)
    zone = np.where((lon > starts) < 1)[0].min()
    projstr = '+proj=utm +zone=%i +%s +ellps=WGS84 +datum=WGS84 +units=m +no_defs' % (zone,hemi)
    return projstr


def geo_to_utm(shape,utmstr=None):
    if utmstr is None:
        point = shape.centroid
        utmstr = get_utm_proj(point.y,point.x)
    project = partial(
        pyproj.transform,
        pyproj.Proj('+proj=longlat +ellps=WGS84 +datum=WGS84 +units=degrees'),
        pyproj.Proj(utmstr))

    pshape = transform(project,shape)
    return (pshape,utmstr)

def utm_to_geo(pshape,utmstr):
    reverse = partial(
        pyproj.transform,
        pyproj.Proj(utmstr),
        pyproj.Proj('+proj=longlat +ellps=WGS84 +datum=WGS84 +units=degrees'),)
    shape = transform(reverse,pshape)
    return shape
    
