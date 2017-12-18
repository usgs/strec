#!/usr/bin/env python

from strec.proj import get_utm_proj, geo_to_utm, utm_to_geo
from shapely.geometry import Point, Polygon
import numpy as np


def test_get_utm_proj():
    lat = 36
    lon = -123
    utm_proj = get_utm_proj(lat, lon)
    assert utm_proj == '+proj=utm +zone=10 +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs'

    lat = -36
    lon = -93
    utm_proj = get_utm_proj(lat, lon)
    assert utm_proj == '+proj=utm +zone=15 +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs'


def test_geo_to_utm():
    lat = 36
    lon = -123
    point = Point(lon, lat)
    utm_point, utmstr = geo_to_utm(point)
    assert utm_point.x == 500000.0
    assert utm_point.y == 3983948.4533356656
    assert utmstr == '+proj=utm +zone=10 +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs'

    utm_point, utmstr2 = geo_to_utm(point, utmstr)
    assert utm_point.x == 500000.0
    assert utm_point.y == 3983948.4533356656
    assert utmstr2 == '+proj=utm +zone=10 +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs'

    polygon = Polygon([(-124, 35), (-124, 36), (-123, 36), (-123, 35)])
    utm_polygon, utmstr = geo_to_utm(polygon)
    coords = [(408746.74716607813, 3873499.8508478715),
              (409870.9505897423, 3984410.7880757754),
              (500000.0, 3983948.4533356656),
              (500000.0, 3873043.0645342614),
              (408746.74716607813, 3873499.8508478715)]
    x, y = zip(*utm_polygon.exterior.coords[:])
    x = np.array(x)
    y = np.array(y)
    x1, y1 = zip(*coords)
    x1 = np.array(x1)
    y1 = np.array(y1)
    np.testing.assert_almost_equal(x, x1)
    np.testing.assert_almost_equal(y, y1)
    assert utmstr == '+proj=utm +zone=10 +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs'


def test_utm_to_geo():
    x = 500000.0
    y = 3983948.4533356656
    utm_point = Point(x, y)
    utmstr = '+proj=utm +zone=10 +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs'
    geo_point = utm_to_geo(utm_point, utmstr)
    assert geo_point.x == -123.00000000000001
    assert geo_point.y == 36.0

    utm_poly = Polygon([(408746.74716607813, 3873499.8508478715),
                        (409870.9505897423, 3984410.7880757754),
                        (500000.0, 3983948.4533356656),
                        (500000.0, 3873043.0645342614),
                        (408746.74716607813, 3873499.8508478715)])
    geo_poly = utm_to_geo(utm_poly, utmstr)
    coords = [(-124.0, 34.999999999999986),
              (-124.0, 35.99999999999999),
              (-123.00000000000001, 36.0),
              (-123.00000000000001, 35.0),
              (-124.0, 34.999999999999986)]

    x, y = zip(*geo_poly.exterior.coords[:])
    x = np.array(x)
    y = np.array(y)
    x1, y1 = zip(*coords)
    x1 = np.array(x1)
    y1 = np.array(y1)
    np.testing.assert_almost_equal(x, x1)
    np.testing.assert_almost_equal(y, y1)


if __name__ == '__main__':
    test_get_utm_proj()
    test_geo_to_utm()
    test_utm_to_geo()
