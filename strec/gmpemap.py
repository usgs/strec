#!/usr/bin/env python

#stdlib imports
import urllib2
import urllib
import sys
from xml.dom.minidom import parseString
import os.path
import re
from math import *

#local imports
from utils import *

#third party imports
import matplotlib.pylab as plt

def plotPolygon(lat,lon,poly,regnum,plotFile):
    fig = plt.figure(figsize=(6,6))
    px = [pol[0] for pol in poly]
    py = [pol[1] for pol in poly]
    plt.plot(px,py,'b')
    plt.hold(True)
    plt.plot(lon,lat,'rx')
    plt.title('%.4f,%.4f in Region %i' % (lat,lon,regnum))
    plt.savefig(plotFile)
    plt.close()    

def getFERegion(lat,lon,config,homedir,plotFile=None):
    """
    Return FE region number describing Flinn-Engdahl region of input point.
    @param lat: Earthquake latitude.
    @param lon: Earthquake longitude.
    @param config: config file object (Used to obtain location of FE data file).
    @param homedir: Used with config to obtain location of FE data file
    @keyword plotFile: If this is specified, make a plot of the FE region with the EQ point in it.
    @return: tuple of (regnum,regname) Numerical code for FE region.
    """
    fefile = os.path.join(homedir,'data',config.get('FILES','coords'))
    f = open(fefile,'rt')
    poly = []
    checkInterior = False
    for line in f.readlines():
        if line.find('>>') > -1:
            if line.lower().find('interior') > -1:
                #interior ring, regnum stays the same BUT if we're inside the interior ring, we are NOT
                #inside the polygon indicated by this number!!
                inside,dmin = inPolygon(lon,lat,poly)
                #the polygon we just checked is the enclosing one, not the interior ring.
                if inside:
                    checkInterior = True
                    poly = []
                    continue
                else:
                    poly = []
                    continue
            if len(poly):
                inside,dmin = inPolygon(lon,lat,poly)
                keepGoing = False
                if checkInterior:
                    if inside:
                        checkInterior = False
                        parts = line.split()
                        regnum = int(parts[1])
                        subpart = int(parts[2])
                        poly = []
                        continue
                    else:
                        f.close()
                        if plotFile is not None:
                            plotPolygon(lat,lon,poly,regnum,plotFile)
                        return regnum
                else:
                    if inside:
                        f.close()
                        if plotFile is not None:
                            plotPolygon(lat,lon,poly,regnum,plotFile)
                        return regnum
                    else:
                        parts = line.split()
                        regnum = int(parts[1])
                        subpart = int(parts[2])
                        poly = []
                        continue
            else:
                parts = line.split()
                regnum = int(parts[1])
                subpart = int(parts[2])
                poly = []
                continue
        parts = line.split()
        poly.append((float(parts[0]),float(parts[1])))
        continue

    if len(poly):
        inside,dmin = inPolygon(lon,lat,poly)
        if inside:
            f.close()
            return regnum
        else:
            f.close()
            return None

def getTectonicRegime(feregnum,config,homedir):
    """
    Return a dictionary with information about the tectonic regime of an FE region.
    @param feregnum: FE region number.
    @return: Dictionary containing fields 'name' and 'code'.
    """
    #Look up which tectonic regime "contains" this FE region number
    gmpefile = os.path.join(homedir,'data',config.get('FILES','fecodes'))
    f = open(gmpefile,'rt')
    f.readline()
    trdict = None
    for line in f.readlines():
        parts = splitWithCommas(line)
        fegr = int(parts[0])
        if fegr != feregnum:
            continue
        trdict = fillDict(parts,config)
        break
    f.close()
    return trdict

def getTectonicRegimeByNumber(typenum,config,homedir):
    """
    Return a dictionary with information about the tectonic regime of an FE region.
    @param typenum: TR type number.
    @return: Dictionary containing fields 'name' and 'code'.
    """
    #Look up which tectonic regime "contains" this FE region number
    gmpefile = os.path.join(homedir,'data',config.get('FILES','fecodes'))
    f = open(gmpefile,'rt')
    f.readline()
    for line in f.readlines():
        parts = splitWithCommas(line)
        trnum = int(parts[2])
        if trnum != typenum:
            continue
        trdict = fillDict(parts,config)
    f.close()
    return trdict

def fillDict(parts,config):
    code = int(parts[2])
    feregname = parts[1]
    name = config.get('REGIMES',str(code))
    slabflag = parts[3]
    scrflag = int(parts[4])
    splitflag = int(parts[5])
    depths = [parts[6],parts[8],parts[10]]
    gmpes = [parts[7],parts[9],parts[11]]
    warning = parts[12][0:-1]
    trdict = {}
    trdict['name'] = name.replace('"','')
    trdict['feregname'] = feregname.replace('"','')
    trdict['code'] = code
    trdict['slabflag'] = slabflag
    trdict['scrflag'] = scrflag
    trdict['splitflag'] = splitflag
    trdict['depths'] = depths
    trdict['gmpes'] = gmpes
    trdict['warning'] = warning
    return trdict

def eventInStablePolygon(lat,lon,config,homedir):
    polyfile = os.path.join(homedir,'data',config.get('FILES','polygons'))
    polygon = None
    xylist = []
    f = open(polyfile,'rt')
    linesread = f.readlines()
    f.close()
    for line in linesread:
        if line.startswith('>>'):
            if len(xylist):
                inpoly,dmin = inPolygon(lon,lat,xylist)
                if inpoly: #and dmin <= SCR_DIST then return (False,polygon,
                    return (True,polygon,dmin)
            m = re.search('\([A-Z]+\)',line)
            polygon = line[m.start()+1:m.end()-1]
            xylist = []
            continue
        parts = line.split()
        xylist.append((float(parts[0]),float(parts[1])))
        continue
    return (False,None,None)

def eventInFEGRPolygon(lat,lon,homedir,config):
    polyfile = os.path.join(homedir,'data',config.get('FILES','fegrs'))
    polygon = None
    xylist = []
    f = open(polyfile,'rt')
    linesread = f.readlines()
    f.close()
    hasRegion = False
    hasCategory = False
    region = None
    category = None
    xylist = []
    for line in linesread:
        parts = line.split()
        if len(parts) == 1:
            if not hasRegion:
                hasRegion = True
                region = int(parts[0])
                continue
            if not hasCategory:
                hasCategory = True
                category = int(parts[0])
                continue
        if len(parts) == 2:
            xylist.append((float(parts[0]),float(parts[1])))
            continue
        if len(parts) == 0:
            if region == 162:
                pass
            inpoly,dmin = inPolygon(lon,lat,xylist)
            if inpoly:
                return (True,region,category,dmin)
            hasCategory = False
            hasRegion = False
            xylist = []

    return (False,None,None,0.0)

def getAzimuth(lat1,lon1,lat2,lon2):
    """
    Get the numerical compass direction between two points.
    @param lat1: Latitude of first point.
    @param lon1: Longitude of first point.
    @param lat2: Latitude of second point.
    @param lon2: Longitude of second point.
    @return: Numerical compass direction between two input points.
    """
    DE2RA = 0.01745329252 
    RA2DE = 57.2957795129
    lat1 = lat1 * DE2RA
    lat2 = lat2 * DE2RA
    lon1 = lon1 * DE2RA
    lon2 = lon2 * DE2RA
    
    ilat1 = floor(0.50 + lat1 * 360000.0)
    ilat2 = floor(0.50 + lat2 * 360000.0)
    ilon1 = floor(0.50 + lon1 * 360000.0)
    ilon2 = floor(0.50 + lon2 * 360000.0)
    
    result = 0
    
    if ((ilat1 == ilat2) and (ilon1 == ilon2)):
        return result
    elif (ilon1 == ilon2):
         if (ilat1 > ilat2):
             result = 180.0

    else:
       c = acos(sin(lat2)*sin(lat1) + cos(lat2)*cos(lat1)*cos((lon2-lon1)))
       A = asin(cos(lat2)*sin((lon2-lon1))/sin(c))
       result = (A * RA2DE)

       if (ilat2 > ilat1) and (ilon2 > ilon1):
          pass
       elif ((ilat2 < ilat1) and (ilon2 < ilon1)):
         result = 180.0 - result
       elif ((ilat2 < ilat1) and (ilon2 > ilon1)):
         result = 180.0 - result
       elif ((ilat2 > ilat1) and (ilon2 < ilon1)):
         result = result + 360.0

    if result < 0:
       result = result + 360

    return result

def sdist(lat1,lon1,lat2,lon2):
    """
    Approximate great circle distance (meters) assuming spherical Earth (6367 km radius).
    @param lat1: Latitude of first point.
    @param lon1: Longitude of first point.
    @param lat2: Latitude of second point.
    @param lon2: Longitude of second point.
    @return: Vector of great circle distances, same length as longer of two input arrays of points.
    """		
    R = 6367*1e3 #radius of the earth in meters, assuming spheroid
    dlon = lon1-lon2;
    t1 = pow((cosd(lat2)*sind(dlon)),2);
    t2 = pow((cosd(lat1)*sind(lat2) - sind(lat1)*cosd(lat2)*cosd(dlon)),2);
    t3 = sind(lat1)*sind(lat2) + cosd(lat1)*cosd(lat2)*cosd(dlon);
    
    dsig = atan2(sqrt(t1+t2),t3)
    
    gcdist = R*dsig;
    return gcdist

def inPolygon(x,y,poly):
    """
    Point-in-Polygon routine scraped from the web.
    @param x: Input x coordinate.
    @param y: Input y coordinate.
    @param poly: list of (x,y) pairs.
    @return: Tuple of (inside,dmin) where inside is a boolean, and dmin is the
             shortest distance between (x,y) and any of the polygon vertices.
    """
    n = len(poly)
    inside =False
    dmin = 999999999
    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if p2x != p1x and p2y != p1y:
            dp1 = sdist(p1y,p1x,y,x)/1000.0
            dp2 = sdist(p2y,p2x,y,x)/1000.0
            if min(dp1,dp2) < dmin:
                dmin = min(dp1,dp2)
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return (inside,dmin)

def normAngle(angle):
    if angle > 360:
        angle = angle-360
    if angle < 0:
        angle = angle+360
    return angle

if __name__ == '__main__':
    lat = float(sys.argv[1])
    lon = float(sys.argv[2])
    regnum = getFERegion(lat,lon)
    print regnum
