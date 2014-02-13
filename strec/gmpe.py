#!/usr/bin/env python

#stdlib imports
import re
import urllib2
from xml.dom.minidom import parseString,parse
import datetime
import urllib
import time
import os.path
import sys
import copy
import ConfigParser
from optparse import OptionParser
import csv
import StringIO

#third party imports
from scipy.io import netcdf
import numpy

#import local modules
from utils import *
from gmpemap import *
from cmt import *

class StrecResults(object):
    TimeFormat = '%Y-%m-%d %H:%M:%S'
    def __init__(self,lat,lon,depth,mag,etime,eqtype,fmstring,regdict,trdict,plungevals,slabvals,eqdict,warning,mtsource):
        self.rdict = {}
        self.rdict['Latitude'] = lat
        self.rdict['Longitude'] = lon
        self.rdict['Depth'] = depth
        self.rdict['Magnitude'] = mag
        self.rdict['Time'] = etime
        self.rdict['EarthquakeType'] = eqtype
        self.rdict['FocalMechanism'] = fmstring
        self.rdict['FERegionName'] = regdict['name']
        self.rdict['FERegionNumber'] = regdict['number']
        self.rdict['TectonicRegimeName'] = trdict['name'] #Is this a duplicate of 'EarthquakeType'?
        self.rdict['TectonicRegimeCode'] = trdict['code']
        self.rdict['TectonicRegimeSlabFlag'] = trdict['slabflag']
        self.rdict['TectonicRegimeSCRFlag'] = trdict['scrflag']
        self.rdict['TectonicRegimeSplitFlag'] = trdict['splitflag']
        self.rdict['TectonicRegimeDepths'] = trdict['depths']
        self.rdict['TectonicRegimeRegimes'] = trdict['gmpes']
        self.rdict['TectonicRegimeWarning'] = trdict['warning']
        self.rdict['TAxisPlunge'] = plungevals['T']['plunge']
        self.rdict['TAxisAzimuth'] = plungevals['T']['azimuth']
        self.rdict['NAxisPlunge'] = plungevals['N']['plunge']
        self.rdict['NAxisAzimuth'] = plungevals['N']['azimuth']
        self.rdict['PAxisPlunge'] = plungevals['P']['plunge']
        self.rdict['PAxisAzimuth'] = plungevals['P']['azimuth']
        self.rdict['NodalPlane1Strike'] = plungevals['NP1']['strike']
        self.rdict['NodalPlane1Dip'] = plungevals['NP1']['dip']
        self.rdict['NodalPlane1Rake'] = plungevals['NP1']['rake']
        self.rdict['NodalPlane2Strike'] = plungevals['NP2']['strike']
        self.rdict['NodalPlane2Dip'] = plungevals['NP2']['dip']
        self.rdict['NodalPlane2Rake'] = plungevals['NP2']['rake']
        self.rdict['SlabStrike'] = slabvals['strike']
        self.rdict['SlabDip'] = slabvals['dip']
        self.rdict['SlabDepth'] = slabvals['depth']
        self.rdict['InterfaceConditionsMet'] = eqdict['eq2']
        self.rdict['InterfaceDepthInterval'] = eqdict['eq3a']
        self.rdict['IntraslabDepthInterval'] = eqdict['eq3b']
        self.rdict['Warning'] = warning
        self.rdict['MomentTensorSource'] = mtsource

    def __getitem__(self,key):
        return self.rdict[key]

    def __setitem__(self,key,value):
        self.rdict[key] = value

    def __eq__(self,other):
        impkeys = ['MomentTensorSource','FocalMechanism','EarthquakeType',
        'FERegionNumber','FERegionName',
        'TAxisPlunge','TAxisAzimuth',
        'NAxisPlunge','NAxisAzimuth',
        'PAxisPlunge','PAxisAzimuth',
        'NodalPlane1Strike','NodalPlane1Dip','NodalPlane1Rake',
        'NodalPlane2Strike','NodalPlane2Dip','NodalPlane2Rake']
        isDiff = False
        for key in impkeys:
            if self[key] != other[key]:
                isDiff = True
                break
        return isDiff

    def readFromCSV(self,line,currentTime=False):
        fobj = StringIO.StringIO(line)
        reader = csv.reader(fobj)
        row = reader.next()
        if currentTime:
            offset = 1
            ptime = datetime.datetime.strptime(row[0],self.TimeFormat)
        else:
            ptime = None
            offset = 0
        keys = collections.OrderedDict(
            {'Time':'time',
             'Latitude':'float',
             'Longitude':'float',
             'Depth':'float',
             'Magnitude':'float',
             'EarthquakeType':'string',
             'FocalMechanism':'string',
             'FERegionName':'string',
             'FERegionNumber':'string',
             'TAxisPlunge':'float',
             'TAxisAzimuth':'float',
             'NAxisPlunge':'float',
             'NAxisAzimuth':'float',
             'PAxisPlunge':'float',
             'PAxisAzimuth':'float',
             'NodalPlane1Strike':'float',
             'NodalPlane1Dip':'float',
             'NodalPlane1Rake':'float',
             'NodalPlane2Strike':'float',
             'NodalPlane2Dip':'float',
             'NodalPlane2Rake':'float',
             'SlabStrike':'float',
             'SlabDip':'float',
             'SlabDepth':'float',
             'Eq2':'string',
             'Eq3a':'string',
             'Eq3b':'string',
             'Warning':'string'})
        
        for key,keytype in keys.iteritems():
            if keytype == 'time':
                self.rdict[key] = datetime.datetime.strptime(row[offset],self.TimeFormat)
            elif keytype == 'float':
                self.rdict[key] = float(row[offset])
            else: #default is string
                self.rdict[key] = row[offset]
            offset += 1
        fobj.close()
        return ptime

    def renderCSV(self,fobj,currentTime=False):
        lat = self.rdict['Latitude']
        lon = self.rdict['Longitude']
        depth = self.rdict['Depth']
        mag = self.rdict['Magnitude']
        etime = self.rdict['Time']

        gmpe = self.rdict['EarthquakeType']
        fmstring = self.rdict['FocalMechanism']
        regname = self.rdict['TectonicRegimeName']
        regnumber = self.rdict['TectonicRegimeCode']
        
        tp = self.rdict['TAxisPlunge']
        ta = self.rdict['TAxisAzimuth']
        np = self.rdict['NAxisPlunge']
        na = self.rdict['NAxisAzimuth']
        pp = self.rdict['PAxisPlunge']
        pa = self.rdict['PAxisAzimuth']
        np1s = self.rdict['NodalPlane1Strike']
        np1d = self.rdict['NodalPlane1Dip']
        np1r = self.rdict['NodalPlane1Rake']

        np2s = self.rdict['NodalPlane2Strike']
        np2d = self.rdict['NodalPlane2Dip']
        np2r = self.rdict['NodalPlane2Rake']

        slabstrike = self.rdict['SlabStrike']
        slabdip = self.rdict['SlabDip']
        slabdepth = self.rdict['SlabDepth']

        eq2 = self.rdict['InterfaceConditionsMet']
        eq3a = self.rdict['InterfaceDepthInterval']
        eq3b = self.rdict['IntraslabDepthInterval']
        warning = self.rdict['Warning']

        if not currentTime:
            fmt = '%s,%.4f,%.4f,%.1f,%.1f, %s,%s,"%s",%i, %.1f,%.1f,%.1f,%.1f,%.1f,%.1f, %.1f,%.1f,%.1f,%.1f,%.1f,%.1f, %.1f,%.1f,%.1f  ,%s,%s,%s,"%s"\n'
            tpl = (etime,lat,lon,depth,mag,
                   gmpe,fmstring,regname,regnumber,
                   ta,tp,na,np,pa,pp,
                   np1s,np1d,np1r,np2s,np2d,np2r,slabstrike,slabdip,slabdepth,eq2,eq3a,eq3b,warning)
            fobj.write(fmt % tpl)
        else:
            fmt = '%s,%s,%.4f,%.4f,%.1f,%.1f, %s,%s,"%s",%i, %.1f,%.1f,%.1f,%.1f,%.1f,%.1f, %.1f,%.1f,%.1f,%.1f,%.1f,%.1f, %.1f,%.1f,%.1f  ,%s,%s,%s,"%s"\n'
            ptime = datetime.datetime.utcnow().strftime(self.TimeFormat)
            tpl = (ptime,etime,lat,lon,depth,mag,
                   gmpe,fmstring,regname,regnumber,
                   ta,tp,na,np,pa,pp,
                   np1s,np1d,np1r,np2s,np2d,np2r,slabstrike,slabdip,slabdepth,eq2,eq3a,eq3b,warning)
            fobj.write(fmt % tpl)
            

    def renderXML(self,fobj):
        fobj.write('<?xml version="1.0" encoding="US-ASCII" standalone="yes"?>\n')
        fobj.write('<gmpeinfo>\n')
        if self.rdict['Time'] is None:
            tstr = 'Unknown'
        else:
            tstr = self.rdict['Time'].strftime(self.TimeFormat)
        lat = self.rdict['Latitude']
        lon = self.rdict['Longitude']
        depth = self.rdict['Depth']
        mag = self.rdict['Magnitude']

        gmpe = self.rdict['EarthquakeType']
        fmstring = self.rdict['FocalMechanism']
        regname = self.rdict['TectonicRegimeName']
        regnumber = self.rdict['FERegionNumber']
        
        tpl = (lat,lon,depth,mag,tstr)
        fobj.write('<eqinfo lat="%.4f" lon="%.4f" depth="%.1f" magnitude="%.1f" time="%s"/>\n' % tpl)
        tpl = (self.rdict['SlabStrike'],self.rdict['SlabDip'],self.rdict['SlabDepth'])
        fobj.write('<slabinfo strike="%.2f" dip="%.2f" depth="%.1f"/>\n' % tpl)
        fobj.write('\t<earthquakeType>%s</earthquakeType>\n' % gmpe)
        fobj.write('\t<focalMechanism>%s</focalMechanism>\n' % fmstring)
        fobj.write('\t<feregion>%i</feregion>\n' % regnumber)
        fobj.write('\t<fename>%s</fename>\n' % self.rdict['FERegionName'])
        fobj.write('\t<domain>%s</domain>\n' % self.rdict['TectonicRegimeName'])
        fobj.write('\t<momentTensorSource>%s</momentTensorSource>\n' % self.rdict['MomentTensorSource'])
        fobj.write('\t<plungevalues>\n')
        if self.rdict['TAxisPlunge'] is not None:
            tp = self.rdict['TAxisPlunge']
            ta = self.rdict['TAxisAzimuth']
            np = self.rdict['NAxisPlunge']
            na = self.rdict['NAxisAzimuth']
            pp = self.rdict['PAxisPlunge']
            pa = self.rdict['PAxisAzimuth']
            np1s = self.rdict['NodalPlane1Strike']
            np1d = self.rdict['NodalPlane1Dip']
            np1r = self.rdict['NodalPlane1Rake']
            
            np2s = self.rdict['NodalPlane2Strike']
            np2d = self.rdict['NodalPlane2Dip']
            np2r = self.rdict['NodalPlane2Rake']
            fobj.write('\t\t<tAxis azimuth="%.0f" plunge="%.0f"/>\n' % (ta,tp))
            fobj.write('\t\t<pAxis azimuth="%.0f" plunge="%.0f"/>\n' % (pa,pp))
            fobj.write('\t\t<nAxis azimuth="%.0f" plunge="%.0f"/>\n' % (na,np))

            fmt1 = '\t\t<nodalplane1 strike="%.0f" dip="%.0f" slip="%.0f"/>\n'
            tpl1 = (np1s,np1d,np1r)
            fmt2 = '\t\t<nodalplane2 strike="%.0f" dip="%.0f" slip="%.0f"/>\n'
            tpl2 = (np2s,np2d,np2r)
            fobj.write(fmt1 % tpl1)
            fobj.write(fmt2 % tpl2)
        else:
            fobj.write('\t\t<tAxis azimuth="NaN" plunge="NaN"/>\n')
            fobj.write('\t\t<pAxis azimuth="NaN" plunge="NaN"/>\n')
            fobj.write('\t\t<nAxis azimuth="NaN" plunge="NaN"/>\n')
            fobj.write('\t\t<nodalplane1 strike="NaN" dip="NaN" slip="NaN"/>\n')
            fobj.write('\t\t<nodalplane2 strike="NaN" dip="NaN" slip="NaN"/>\n')
        fobj.write('\t</plungevalues>\n')
        fobj.write('\t<!--eq2: Focal mechanism satisfies interface conditions.-->\n')
        fobj.write('\t<!--eq3a: Depth within interface depth interval.-->\n')
        fobj.write('\t<!--eq3b: Depth within intraslab depth interval.-->\n')
        tpl = (self.rdict['InterfaceConditionsMet'],self.rdict['InterfaceDepthInterval'],
               self.rdict['IntraslabDepthInterval'])
        fobj.write('\t<equations eq2="%s" eq3a="%s" eq3b="%s"/>\n' % tpl)
        fobj.write('\t<warning>%s</warning>\n' % self.rdict['Warning'])
        fobj.write('</gmpeinfo>\n')

    def renderPretty(self,fobj):
        if self.rdict['Time'] is None:
            fobj.write( 'Time: Unknown\n')
        else:
            fobj.write( 'Time: %s\n' % self.rdict['Time'])
        fobj.write( 'Lat: %s\n' % self.rdict['Latitude'])
        fobj.write( 'Lon: %s\n' % self.rdict['Longitude'])
        fobj.write( 'Depth: %s\n' % self.rdict['Depth'])
        fobj.write( 'Magnitude: %s\n' % self.rdict['Magnitude'])
        fobj.write( 'Earthquake Type: %s\n' % self.rdict['EarthquakeType'])
        fobj.write( 'Focal Mechanism: %s\n' % self.rdict['FocalMechanism'])
        fobj.write( 'FE Region Name: %s\n' % self.rdict['FERegionName'])
        fobj.write( 'FE Region Number: %i\n' % self.rdict['FERegionNumber'])
        fobj.write( 'FE Seismotectonic Domain: %s\n' % self.rdict['TectonicRegimeName'])
        fobj.write( 'Focal Mechanism:\n')
        if self.rdict['TAxisAzimuth'] is None:
            fobj.write( 'No Focal Mechanism determined\n')
        else:
            tensordict = {'gcmt':'Global Centroid Moment Tensor',
                          'wphase':'USGS W-Phase Moment Tensor',
                          'usgs':'USGS Centroid Moment Tensor',
                          'body':'USGS Body Wave Moment Tensor',
                          'region':'USGS/SLU Regional Moment Tensor',
                          'historical':'Historical solution',
                          'composite':'Composite solution'}
            fobj.write( '\tT Axis Strike and Plunge: %.2f %.2f\n' % (self.rdict['TAxisAzimuth'],self.rdict['TAxisPlunge']))
            fobj.write( '\tP Axis Strike and Plunge: %.2f %.2f\n' % (self.rdict['PAxisAzimuth'],self.rdict['PAxisPlunge']))
            fobj.write( '\tN Axis Strike and Plunge: %.2f %.2f\n' % (self.rdict['NAxisAzimuth'],self.rdict['NAxisPlunge']))
            fmt1 = '\tFirst Nodal Plane strike,dip,rake: %.2f %.2f %.2f\n'
            tpl1 = (self.rdict['NodalPlane1Strike'],self.rdict['NodalPlane1Dip'],self.rdict['NodalPlane1Rake'])
            fobj.write( fmt1 % tpl1)
            fmt2 = '\tSecond Nodal Plane strike,dip,rake: %.2f %.2f %.2f\n'
            tpl2 = (self.rdict['NodalPlane2Strike'],self.rdict['NodalPlane2Dip'],self.rdict['NodalPlane2Rake'])
            fobj.write( fmt2 % tpl2)
            fobj.write( '\tMoment Source: %s\n' % self.rdict['MomentTensorSource'])
        fobj.write( 'Slab Parameters:\n')
        fobj.write( '\tStrike Dip Depth: %.2f %.2f %.2f\n' % (self.rdict['SlabStrike'],
                                                              self.rdict['SlabDip'],
                                                              self.rdict['SlabDepth']))
        fobj.write( 'Focal mechanism satisfies interface conditions: %s\n' % self.rdict['InterfaceConditionsMet'])
        fobj.write( 'Depth within interface depth interval: %s\n' % self.rdict['InterfaceDepthInterval'])
        fobj.write( 'Depth within intraslab depth interval: %s\n' % self.rdict['IntraslabDepthInterval'])
        fobj.write( 'Warning: %s\n' % self.rdict['Warning'])

class GMPESelector(object):
    Config = None
    dbfile = None
    def __init__(self,configfile,dbfile,datafolder):
        self.Config = config = ConfigParser.ConfigParser()
        self.Config.readfp(open(configfile))
        self.dbfile = dbfile
        self.homedir = os.path.dirname(os.path.abspath(__file__)) #where is this file?
        self.datafolder = datafolder

    def selectGMPE(self,lat,lon,depth,magnitude,date=None,forceComposite=False,plungevals=None):
        """
        @param lat Earthquake latitude
        @param lon Earthquake longitude
        @param depth Earthquake depth
        @param magnitude Earthquake depth
        @keyword date Optional datetime object indicating the origin time of the event.  Default is None.
        @keyword forceComposite Boolean indicating whether focal mechanism determination should be forced to be composite.
        @keyword plungevals Dictionary containing the key parameters of a focal mechanism solution (Axes ['plunge','azimuth'] and nodal planes ['strike','dip','rake']).
        @return Tuple containing values:
                - gmpe Name of GMPE (ACRsh, etc.)
                - fmstring  Focal Mechanism: ('SS','RS','NM', or 'N/A')
                - regdict Flinn-Engdahl Region Dictionary, containing two keys: "name" and "number"
                - trdict Tectonic Regime dictionary, containing fields:
                         - name ('SCR (generic)', 'ACR (shallow)', etc.)
                         - code
                         - slabflag
                         - scrflag
                         - splitflag
                         - depths List of depth ranges for GMPEs
                         - gmpes List of GMPE strings for each depth range.
                         - warning Warning text, if any.
                - plungevals None, or Dictionary containing the following fields:
                         - 'T' Dictionary of 'azimuth' and 'plunge' values for the T axis.
                         - 'N' Dictionary of 'azimuth' and 'plunge' values for the N(B) axis.
                         - 'P' Dictionary of 'azimuth' and 'plunge' values for the P axis.
                         - 'NP1' Dictionary of angles for the first nodal plane ('strike','dip','rake')
                         - 'NP2' Dictionary of angles for the second nodal plane ('strike','dip','rake')
                - slabvals Dictionary of slab value paramers: 'strike','dip','depth'
                - eqdict   Dictionary of results from Eq2, Eq3a, and Eq3b. i.e., {'eq2':True,'eq3a':True,'eq3b':True}
                - warning Either empty if GMPE selection is ok, or 'WARNING' if the GMPE selection algorithm fell through.
        """
        if plungevals is None:
            if date is None or forceComposite:
                plungevals,fmwarning,mtsource = self.getFocMechAxes(lat,lon,depth,magnitude)
            else:
                plungevals,fmwarning,mtsource = self.getFocMechAxes(lat,lon,depth,magnitude,date=date)
        else:
            mtsource = 'input'
            fmwarning = ''
        if plungevals is None:
            plungevals = {'T':{},'N':{},'P':{},'NP1':{},'NP2':{}}
            plungevals['T']['plunge'] = numpy.nan
            plungevals['T']['azimuth'] = numpy.nan
            plungevals['N']['plunge'] = numpy.nan
            plungevals['N']['azimuth'] = numpy.nan
            plungevals['P']['plunge'] = numpy.nan
            plungevals['P']['azimuth'] = numpy.nan
            plungevals['NP1']['strike'] = numpy.nan
            plungevals['NP1']['dip'] = numpy.nan
            plungevals['NP1']['rake'] = numpy.nan
            plungevals['NP2']['strike'] = numpy.nan
            plungevals['NP2']['dip'] = numpy.nan
            plungevals['NP2']['rake'] = numpy.nan
        eqdict = {'eq2':None,'eq3a':None,'eq3b':None}
        fmstring  = self.getFocalMechanism(plungevals)
        feregnum = getFERegion(lat,lon,self.Config,self.homedir)
        trdict = getTectonicRegime(feregnum,self.Config,self.homedir)
        regdict = {'number':feregnum,'name':trdict['feregname'].strip()}
        slabvals = {'strike':float('nan'),'dip':float('nan'),'depth':float('nan')}
        mindist = None
        distwarning = ''
        if trdict['scrflag']: #does this region have a flag noting that part of the region is stable and part something else?
            inpoly,polyname,mindist = eventInStablePolygon(lat,lon,self.Config,self.homedir)
            SCR_DIST = float(self.Config.get('CONSTANTS','SCR_DIST'))
            if inpoly and mindist < SCR_DIST:
                inpoly = False
                distwarning = 'WARNING: Event is less than %.1f kilometers from the edge of a stable polygon' % SCR_DIST
            if inpoly:
                if trdict['scrflag'] == 1:
                    SCR_REGIME1 = int(self.Config.get('CONSTANTS','SCR_REGIME1'))
                    trdict2 = getTectonicRegimeByNumber(SCR_REGIME1,self.Config,self.homedir)
                    trdict = copy.copy(trdict2)
                else:
                    SCR_REGIME2 = int(self.Config.get('CONSTANTS','SCR_REGIME2'))
                    trdict2 = getTectonicRegimeByNumber(SCR_REGIME2,self.Config,self.homedir)
                    gmpe,warning = self.getGMPE(trdict2,depth)
                    warning = self.combineWarnings(warning,distwarning,fmwarning)
                    sresults = StrecResults(lat,lon,depth,magnitude,date,
                                            gmpe,fmstring,regdict,trdict2,
                                            plungevals,slabvals,eqdict,warning,mtsource)
                    return sresults
            else:
                if trdict['splitflag']:
                    inpoly,fegr,sc,dmin = eventInFEGRPolygon(lat,lon,self.homedir,self.Config)
                    if inpoly:
                        trdict2 = getTectonicRegimeByNumber(sc,self.Config,self.homedir)
                        trdict2['slabflag'] = trdict['slabflag']
                        trdict = copy.copy(trdict2)
                        #fall out to the check for subduction zones
                    else:
                        #fall out to the check for subduction zones
                        pass
                else:
                    #fall out to the check for subduction zones
                    pass
        else:
            if trdict['splitflag']:
                inpoly,fegr,sc,dmin = eventInFEGRPolygon(lat,lon,self.homedir,self.Config)
                if inpoly:
                    trdict2 = getTectonicRegimeByNumber(sc,self.Config,self.homedir)
                    trdict2['slabflag'] = trdict['slabflag']
                    trdict = copy.copy(trdict2)
                    #fall out to the check for subduction zones
                else:
                    #fall out to check for subduction zones
                    pass
            else:
                #fall out to the check for subduction zones
                pass
    
        if trdict['name'].lower().find('sz') == -1: #some variant of active or stable
            gmpe,warning = self.getGMPE(trdict,depth)
            warning = self.combineWarnings(warning,distwarning,fmwarning)
            sresults = StrecResults(lat,lon,depth,magnitude,date,
                                    gmpe,fmstring,regdict,trdict,
                                    plungevals,slabvals,eqdict,warning,mtsource)
            return sresults
        else: #this event probably happened in a subduction zone
            GENERAL_SZ1 = int(self.Config.get('CONSTANTS','SZ_REGIME1'))
            GENERAL_SZ2 = int(self.Config.get('CONSTANTS','SZ_REGIME2'))
            SZ_REGIMEOUT = int(self.Config.get('CONSTANTS','SZ_REGIMEOUT'))
            SZ_REGIMEBACK = int(self.Config.get('CONSTANTS','SZ_REGIMEBACK'))
            if trdict['code'] not in [GENERAL_SZ1,GENERAL_SZ2]: #not actually a subduction zone
                gmpe,warning = self.getGMPE(trdict,depth)
                warning = self.combineWarnings(warning,distwarning,fmwarning)
                sresults = StrecResults(lat,lon,depth,magnitude,date,
                                        gmpe,fmstring,regdict,trdict,
                                        plungevals,slabvals,eqdict,warning,mtsource)
                return sresults
            #at this point, seis. category is either 31 or 34
            slabvals = self.getSlabParams(lat,lon)
            nanlist = []
            for slabval in slabvals:
                if isNaN(slabval['strike']):
                    nanlist.append(1)
                else:
                    nanlist.append(0)
            if len(slabvals) > 1 or sum(nanlist) > 0:
                if sum(nanlist) == len(slabvals): #all slab values are NaN
                    slabvals = slabvals[0]
                    if trdict['code'] == GENERAL_SZ1:
                        trenchinfo = self.getTrenchInfo(lat,lon)
                        if trenchinfo['position'] == 'out':
                            trdict2 = getTectonicRegimeByNumber(SZ_REGIMEOUT,self.Config,self.homedir)
                            gmpe,warning = self.getGMPE(trdict2,depth)
                            if len(warning):
                                if len(distwarning):
                                    warning = distwarning + ',' + warning
                            else:
                                warning = distwarning
                            
                            sresults = StrecResults(lat,lon,depth,magnitude,date,
                                                    gmpe,fmstring,regdict,trdict2,
                                                    plungevals,slabvals,eqdict,warning,mtsource)
                            return sresults
                        else:
                            if trdict['slabflag'] == 'a':
                                trdict2 = getTectonicRegimeByNumber(SZ_REGIMEBACK,self.Config,self.homedir)
                                gmpe,warning = self.getGMPE(trdict2,depth)
                                warning = self.combineWarnings(warning,distwarning,fmwarning)
                                sresults = StrecResults(lat,lon,depth,magnitude,date,
                                                        gmpe,fmstring,regdict,trdict2,
                                                        plungevals,slabvals,eqdict,warning,mtsource)
                                return sresults
                            else: #slabflag is 'c'
                                gmpe,slabvals,eqdict,warning = self.getAllSubductionZoneInfo(lat,lon,depth,plungevals,slabvals,trdict['slabflag'],fmstring,trdict)
                                warning = self.combineWarnings(warning,distwarning,fmwarning)
                                sresults = StrecResults(lat,lon,depth,magnitude,date,
                                                        gmpe,fmstring,regdict,trdict,
                                                        plungevals,slabvals,eqdict,warning,mtsource)
                                return sresults
                    else:#GENERAL_SZ2
                        if trdict['slabflag'] == 'a':
                            trdict2 = getTectonicRegimeByNumber(SZ_REGIMEBACK,self.Config,self.homedir)
                            gmpe,warning = self.getGMPE(trdict2,depth)
                            warning = self.combineWarnings(warning,distwarning,fmwarning)
                            sresults = StrecResults(lat,lon,depth,magnitude,date,
                                                    gmpe,fmstring,regdict,trdict2,
                                                    plungevals,slabvals,eqdict,warning,mtsource)
                            return sresults
                        else: #slabflag is 'c'
                            gmpe,slabvals,eqdict,warning = self.getAllSubductionZoneInfo(lat,lon,depth,plungevals,slabvals,trdict['slabflag'],fmstring,trdict)
                            warning = self.combineWarnings(warning,distwarning,fmwarning)
                            sresults = StrecResults(lat,lon,depth,magnitude,date,
                                                    gmpe,fmstring,regdict,trdict,
                                                    plungevals,slabvals,eqdict,warning,mtsource)
                            return sresults
                else: #some slab values are real
                    #get the slab values with the shallowest depth
                    mindepth = 999
                    minslabval = None
                    for slab in slabvals:
                        if isNaN(slab['depth']):
                            continue
                        if slab['depth'] < mindepth:
                            mindepth = slab['depth']
                            slabval = slab
                    gmpe,slabvals,eqdict,warning = self.getAllSubductionZoneInfo(lat,lon,depth,plungevals,slabval,trdict['slabflag'],fmstring,trdict)
                    warning = self.combineWarnings(warning,distwarning,fmwarning)
                    sresults = StrecResults(lat,lon,depth,magnitude,date,
                                            gmpe,fmstring,regdict,trdict,
                                            plungevals,slabvals,eqdict,warning,mtsource)
                    return sresults
            else: #there is only one set of slab values
                gmpe,slabvals,eqdict,warning = self.getAllSubductionZoneInfo(lat,lon,depth,plungevals,slabvals[0],trdict['slabflag'],fmstring,trdict)
                warning = self.combineWarnings(warning,distwarning,fmwarning)
                sresults = StrecResults(lat,lon,depth,magnitude,date,
                                        gmpe,fmstring,regdict,trdict,
                                        plungevals,slabvals,eqdict,warning,mtsource)
                return sresults

    def combineWarnings(self,warning,distwarning,fmwarning):
        if len(warning):
            if len(distwarning):
                if len(fmwarning):
                    warning = fmwarning + ',' + distwarning + ',' + warning
                else:
                    warning = distwarning + ',' + warning
            else:
                if len(fmwarning):
                    warning = fmwarning + ',' + warning
                else:
                    warning = distwarning
        else:
            if len(distwarning):
                if len(fmwarning):
                    warning = fmwarning + ',' + distwarning
                else:
                    warning = distwarning
            else:
                warning = fmwarning
                             
        return warning

    def getFocMechAxes(self,lat,lon,depth,magnitude,date=None):
        """
        Get the plunge and azimuth angles for three axes, and strike,dip,rake angles for two nodal planes, 
        using one of two mechanisms.
        - Retrieve historical GCMT solution for past recorded earthquake.
        - Retrieve composite CMT solution from multiple past earthquakes near input epicenter.
        @param lat: Earthquake latitude.
        @param lon: Earthquake longitude.
        @param depth: Earthquake depth.
         @param magnitude: Earthquake magnitude.
         @keyword date: Optional datetime object indicating the origin time of the event.  Default is None.
         @return: Dictionary containing the following fields:
                 - 'T' Dictionary of 'azimuth' and 'plunge' values for the T axis.
                 - 'N' Dictionary of 'azimuth' and 'plunge' values for the N(B) axis.
                 - 'P' Dictionary of 'azimuth' and 'plunge' values for the P axis.
                 - 'NP1' Dictionary of angles for the first nodal plane ('strike','dip','rake')
                 - 'NP2' Dictionary of angles for the second nodal plane ('strike','dip','rake')
        """
        minboxhist = float(self.Config.get('CONSTANTS','MINRADIAL_DISTHIST'))
        maxboxhist = float(self.Config.get('CONSTANTS','MAXRADIAL_DISTHIST'))
        dboxhist = float(self.Config.get('CONSTANTS','STEP_DISTHIST'))
        depthboxhist = float(self.Config.get('CONSTANTS','DEPTH_RANGEHIST'))
        twindowhist = float(self.Config.get('CONSTANTS','TIME_THRESHIST'))

        minboxcomp = float(self.Config.get('CONSTANTS','MINRADIAL_DISTCOMP'))
        # 1.00 degrees (~111 km in latitude)
        maxboxcomp = float(self.Config.get('CONSTANTS','MAXRADIAL_DISTCOMP'))
        # Approx. 10 km interval  
        dboxcomp = float(self.Config.get('CONSTANTS','STEP_DISTCOMP'))
        depthboxcomp = float(self.Config.get('CONSTANTS','DEPTH_RANGECOMP'))

        #Minimum number of events required to get composite mechanism
        nmin = float(self.Config.get('CONSTANTS','MINNO_COMP'))
        
        if date is not None:
            plungevalues,fmwarning = getHistoricalCMT(date,self.dbfile,twindow=twindowhist)
            mtsource = 'historical'
        else:
            plungevalues,fmwarning = getCompositeCMT(lat,lon,depth,self.dbfile,
                                                   box=minboxcomp,depthbox=depthboxcomp,
                                                   maxbox=maxboxcomp,dbox=dboxcomp,nmin=nmin)
            mtsource = 'composite'

        return plungevalues,fmwarning,mtsource

    def getAllSubductionZoneInfo(self,lat,lon,depth,plungevals,slabvals,slabflag,fmstring,trdict):
        ACR_REGIMESHALLOW = int(self.Config.get('CONSTANTS','ACR_REGIMESHALLOW'))
        if slabflag == 'c' and isNaN(slabvals['strike']):
            trenchinfo = self.getTrenchInfo(lat,lon)
            slabvals = self.getSZDefaultSlabParams(trenchinfo)
        depthzone = self.getSZDepthZone(depth,float(trdict['depths'][0]),float(trdict['depths'][1]))
        trdict2 = getTectonicRegimeByNumber(ACR_REGIMESHALLOW,self.Config,self.homedir)
        eq2 = self.getEq2(plungevals,slabvals)
        eq3a = self.getEq3a(depth,slabvals)
        eq3b = self.getEq3b(depth,slabvals,float(trdict['depths'][0]))
        eqdict = {'eq2':eq2,'eq3a':eq3a,'eq3b':eq3b}
        gmpe,warning = self.getSZGMPE(fmstring,depthzone,depth,eq2,eq3a,eq3b,float(trdict2['depths'][0]),plungevals)
        return (gmpe,slabvals,eqdict,warning)

    def getSZDefaultSlabParams(self,trenchinfo):
        DEFAULT_SZDIP = float(self.Config.get('CONSTANTS','DEFAULT_SZDIP'))
        h = trenchinfo['mindist'] * tan(DEFAULT_SZDIP*(pi/180.0))
        return {'depth':h,'strike':trenchinfo['minstrike'],'dip':DEFAULT_SZDIP}

    def getSZDepthZone(self,depth,depth1,depth2):
        if depth <= depth1:
            return "shallow"
        elif depth > depth1 and depth <= depth2:
            return "medium"
        else:
            return "deep"

    def getGridValue(self,lat,lon,gridfile):
        f = netcdf.netcdf_file(gridfile,'r')
        ymin,ymax = f.variables['y'].actual_range
        xmin,xmax = f.variables['x'].actual_range
        if lat < ymin or lat > ymax or lon < xmin or lon > xmax:
            f.close()
            return numpy.NaN
        y = f.variables['y'].data
        x = f.variables['x'].data
        z = f.variables['z'].data
        iy = numpy.abs(lat - y).argmin()
        ix = numpy.abs(lon - x).argmin()
        zvalue = z[iy][ix]
        f.close()
        return zvalue

    def getSlabParams(self,lat,lon):
        #lon angles are between 0 and 360
        if lon < 0:
            lon = 360 + lon
        allfiles = os.listdir(self.datafolder)
        regions = []
        for file in allfiles:
            if file.endswith('.grd'):
                if file[0:3] not in regions:
                    regions.append(file[0:3])
        slablist = []
        for region in regions:
            regstrike = os.path.join(self.datafolder,region+'_slab1.0_strclip.grd')
            regdip = os.path.join(self.datafolder,region+'_slab1.0_dipclip.grd')
            regdepth = os.path.join(self.datafolder,region+'_slab1.0_clip.grd')
            strike = self.getGridValue(lat,lon,regstrike)
            if numpy.isnan(strike):
                continue
            else:
                strike = strike-90
                if strike < 0:
                    strike += 360
                dip = self.getGridValue(lat,lon,regdip)*-1 #dips are never negative in our definition
                depth = self.getGridValue(lat,lon,regdepth)*-1 #slab depths are negative downwards
                slablist.append({'strike':strike,'dip':dip,'depth':depth})
        if not len(slablist):
            return [{'strike':float('nan'),'dip':float('nan'),'depth':float('nan')}]
        else:
            return slablist

    def getTrenchInfo(self,lat,lon):
        """
        Returns a dictionary of information about position with respect to a trench.
        @param lat: Latitude
        @param lon: Longitude
        @return: Dictionary with keys::
              - position 'in' or 'out'
              - minlat Latitude of point on trench line closest to epicenter
              - minlon Longitude of point on trench line closest to epicenter
              - minstrike Strike angle of point on trench line closest to epicenter
              - mindist Distance between point on trench line closest to epicenter and epicenter
        """
        trenchfile = os.path.join(self.homedir,'data',self.Config.get('FILES','trenches'))
        f = open(trenchfile,'rt')
        segment = ''
        mindist = 9999999999
        minlat = 999
        minlon = 999
        minstrike = 999
        for line in f.readlines():
            if line.startswith('>'):
                segment = line[1:]
                continue
            parts = line.split()
            slon = float(parts[0])
            slat = float(parts[1])
            strike = float(parts[2])
            d = sdist(lat,lon,slat,slon)/1000.0
            if d < mindist:
                mindist = d
                minlat = slat
                minlon = slon
                minstrike = strike
        f.close()
        lineaz = getAzimuth(minlat,minlon,lat,lon)
        dstrike = minstrike - lineaz
        if dstrike >= 360:
            dstrike = dstrike - 360
        if dstrike < 0:
            dstrike = dstrike + 360
        if dstrike > 0 and dstrike < 180:
            position = 'out'
        else:
            position = 'in'
        return {'position':position,'minlat':minlat,'minlon':minlon,'minstrike':minstrike,'mindist':mindist}

    def getSZGMPE(self,fmstring,depthzone,depth,eq2,eq3a,eq3b,acrdepth,plungevals):
        warning = ''
        if depthzone == 'shallow':
            if fmstring == 'RS':
                if eq2: #eq. 2
                    if eq3a:
                        gmpe = 'SZinter'
                    else:
                        if eq3b:
                            gmpe = 'ACRsh'
                            warning = 'Event near/below interface'
                        else:
                            gmpe = 'ACRsh'
                else:
                    if eq3b:
                        gmpe = 'ACRsh'
                        warning = 'Event near/below interface'
                    else:
                        gmpe = 'ACRsh'
            else: #fmstring is 'SS' or 'NM' or 'ALL'
                if fmstring == 'ALL' and plungevals is None:
                    if eq3a:
                        gmpe = 'SZinter'
                        warning = 'No focal mechanism available'
                    else:
                        if eq3b:
                            gmpe = 'ACRsh'
                            warning = 'Event near/below interface'
                        else:
                            gmpe = 'ACRsh'
                else:
                    if eq3b:
                        gmpe = 'ACRsh'
                        warning = 'Event near/below interface'
                    else:
                        gmpe = 'ACRsh'
        elif depthzone == 'medium':
            if fmstring == 'RS':
                if eq2:
                    if eq3a:
                        gmpe = 'SZinter'
                    else:
                        if eq3b:
                            gmpe = 'SZintra'
                        else:
                            if depth > acrdepth:
                                gmpe = 'ACRde'
                            else:
                                gmpe = 'ACRsh'
                else:
                    if eq3b:
                        gmpe = 'SZintra'
                    else:
                        if depth > acrdepth:
                            gmpe = 'ACRde'
                        else:
                            gmpe = 'ACRsh'
            else:
                if fmstring == 'ALL' and plungevals is None:
                    if eq3a:
                        gmpe = 'SZinter'
                        warning = 'No focal mechanism available'
                    else:
                        if eq3b:
                            gmpe = 'SZintra'
                        else:
                            if depth > acrdepth:
                                gmpe = 'ACRde'
                            else:
                                gmpe = 'ACRsh'
                else:
                    if eq3b:
                        gmpe = 'SZintra'
                    else:
                        if depth > acrdepth:
                            gmpe = 'ACRde'
                        else:
                            gmpe = 'ACRsh'
        elif depthzone == 'deep':
            if eq3b:
                gmpe = 'SZintra'
            else:
                warning = 'Event above interface'
                gmpe = 'SZintra'

        return gmpe,warning

    def getFocalMechanism(self,plungevals):
        """
        Return focal mechanism (strike-slip,normal, or reverse).
        @param plungevals: Dictionary containing the following fields:
               - 'T' Dictionary of 'azimuth' and 'plunge' values for the T axis.
               - 'N' Dictionary of 'azimuth' and 'plunge' values for the N(B) axis.
               - 'P' Dictionary of 'azimuth' and 'plunge' values for the P axis.
               - 'NP1' Dictionary of angles for the first nodal plane ('strike','dip','rake')
               - 'NP2' Dictionary of angles for the second nodal plane ('strike','dip','rake')
        @return: String: 'SS','RS','NM','ALL'.
        """
        if plungevals is None:
            return 'ALL'
        #implement eq 1 here
        Tp = plungevals['T']['plunge']
        Np = plungevals['N']['plunge']
        Pp = plungevals['P']['plunge']
        TPLUNGE_RS = float(self.Config.get('CONSTANTS','TPLUNGE_RS'))
        BPLUNGE_DS = float(self.Config.get('CONSTANTS','BPLUNGE_DS'))
        BPLUNGE_SS = float(self.Config.get('CONSTANTS','BPLUNGE_SS'))
        PPLUNGE_NM = float(self.Config.get('CONSTANTS','PPLUNGE_NM'))
        DELPLUNGE_SS = float(self.Config.get('CONSTANTS','DELPLUNGE_SS'))
        if Tp >= TPLUNGE_RS and Np <= BPLUNGE_DS:
            return 'RS'
        if Np >= BPLUNGE_SS and (Tp >= Pp-DELPLUNGE_SS and Tp <= Pp+DELPLUNGE_SS):
            return 'SS'
        if Pp >= PPLUNGE_NM and Np <= BPLUNGE_DS:
            return 'NM'
        return 'ALL'
    
    def getGMPE(self,trdict,depth):
        """
        Return a GMPE string appropriate for the depth in the input Tectonic Regime.
        @param trdict: Dictionary returned by getTectonicRegime() function.
        @param depth: Input depth of earthquake (km).
        @return: GMPE string appropriate for depth, or None if depth outside range.
        """
        #Each Tectonic regime has a series of depth 
        #ranges and corresponding GMPE strings
        startdep = -1
        for i in range(0,len(trdict['depths'])):
            depS = trdict['depths'][i]
            gmpe = trdict['gmpes'][i]
            if depS == '-':
                return (trdict['warning'],'WARNING:Earthquake depth out of expected FEGR depth range.')
            dep = float(depS)
            if depth > startdep and depth <= dep:
                return (gmpe,'')
        return (None,None)

    def getEq2(self,plungevals,slabvals):
        """
        Implementation of equation 2 - checking to see if this earthquake rupture is along the 3D plane of the slab and is a reverse faulting earthquake.
        @param plungevals: Dictionary returned from getFocMechAxes() function.
        @param slabvals: Dictionary returned from the getSlabParams() function.
        @return: True if the input event rupture is "close" to interface rupture, False if not.
        """
        #implement logic for equation 2 from Daniel's paper
        DSTRIKE = float(self.Config.get('CONSTANTS','DSTRIKE_INTERF'))
        DSLIP = float(self.Config.get('CONSTANTS','DDIP_INTERF'))
        DLAMBDA = float(self.Config.get('CONSTANTS','DLAMBDA'))
        if plungevals is None:
            return False
        a = plungevals['P']['azimuth']
    
	#new set of equations (default slab keeps old format; new Gavin's
	#format uses slabs rotated 90 degrees)
        if (slabvals['dip'] == 17.0):
            b1 = (normAngle((slabvals['strike']-90))-DSTRIKE)
            b2 = (normAngle((slabvals['strike']-90))+DSTRIKE)
            b3 = (normAngle((slabvals['strike']+90))-DSTRIKE)
            b4 = (normAngle((slabvals['strike']+90))+DSTRIKE)
	else:
            b1 = (normAngle((slabvals['strike']))-DSTRIKE)
            b2 = (normAngle((slabvals['strike']))+DSTRIKE)
            b3 = (normAngle((slabvals['strike']))-DSTRIKE)
            b4 = (normAngle((slabvals['strike']))+DSTRIKE)

        if a > 270 and b1 < 90:
            b1 = b1 + 360
        if a > 270 and b2 < 90:
            b2 = b2 + 360
        if a > 270 and b3 < 90:
            b3 = b3 + 360
        if a > 270 and b4 < 90:
            b4 = b4 + 360

        if a < 90 and b1 > 270:
            b1 = b1 - 360
        if a < 90 and b2 > 270:
            b2 = b2 - 360
        if a < 90 and b3 > 270:
            b3 = b3 - 360
        if a < 90 and b4 > 270:
            b4 = b4 - 360
        
        c1 = a >= b1
        c2 = a <= b2
        c3 = a >= b3
        c4 = a <= b4
    
        m2a = (c1 and c2 ) or (c3 and c4)
        m2b = ((plungevals['P']['plunge'] >= slabvals['dip']-DSLIP) and (plungevals['P']['plunge'] <= slabvals['dip']+DSLIP))
        m2c1 = ((plungevals['NP1']['rake'] > 90-DLAMBDA) and (plungevals['NP1']['rake'] < 90+DLAMBDA))
        m2c2 = ((plungevals['NP2']['rake'] > 90-DLAMBDA) and (plungevals['NP2']['rake'] < 90+DLAMBDA))
        if (m2a and m2b and (m2c1 or m2c2)):
            return True
        else:
            return False

    def getEq3a(self,depth,slabvals):
        DDEPTH = float(self.Config.get('CONSTANTS','DDEPTH_INTERF')) # interface depth range
        """
        Check to see if the focal depth is within range of the slab depth.
        @param depth: Depth of current earthquake.
        @param slabvals: Dictionary returned from the getSlabParams() function.
        @return: True if depth is close to slab, False if not.
        """
        #Check to see if the focal depth is within range of the slab depth
        if (depth >= slabvals['depth']-DDEPTH and depth < slabvals['depth']+DDEPTH):
            return True
        else:
            return False

    def getEq3b(self,depth,slabvals,intraslabdepth):
        DDEPTH = float(self.Config.get('CONSTANTS','DDEPTH_INTRA')) # intra-slab depth range
        """
        Check to see if the depth is deeper than the slab.
        @param depth:Depth of current earthquake.
        @param slabvals: Dictionary returned from the getSlabParams() function.
        @return: True if depth is deeper than the slab, False if not.
        """
        if depth >= slabvals['depth']-DDEPTH and depth >= intraslabdepth:
            return True
        else:
            return False

#The entry point for command line usage, mostly for testing.            
if __name__ == '__main__':

    usage = """usage: %prog [options] lat lon depth magnitude [date]
    GCMT Composite Focal Mechanism Solution: %prog lat lon depth magnitude
    GCMT Historical or Composite Focal Mechanism Solution: %prog lat lon depth magnitude [date]
    User-defined, GCMT Historical, or GCMT Composite:%prog -d datafolder lat lon depth magnitude [date]
    """
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--datafile",dest="datafile",
                      metavar="DATAFILE",
                      help="Specify the database (.db) file containing moment tensor solutions.")
    parser.add_option("-c", "--csv-out",
                  action="store_true", dest="outputCsv", default=False,
                  help="print output as csv")

    #optparse freaks out if it sees a negative number.  If the negative number is in the middle of a quoted string,
    #then it's fine.  If it's at the beginning of the quoted string, then it still freaks out.  Here I'm going to move
    #the offending string to the end of the argument list, with a "--" arg in front of it.  I could make the user do this
    #on the command line, but that just seems sort of unfriendly.
    # iargs = -1
#     for i in range(0,len(sys.argv)):
#         arg = sys.argv[i]
#         if re.match('-[0-9]',arg) is not None:
#             iargs = i

#     if iargs > -1:
#         if iargs < len(sys.argv)-1: #the argument string isn't the last one
#             tmp = sys.argv[-1]
#             sys.argv[iargs] = tmp
#             sys.argv[-1] = '--'
#             sys.argv.append(

#     if iargs < len(sys.argv)-1:
#         tmp = sys.argv[-1]
#         sys.argv[-1] = sys.argv[iargs]
#         sys.argv[iargs] = tmp
    (options, args) = parser.parse_args()

    if options.datafile is None:
        homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
        options.datafile = os.path.join(homedir,'data','gcmt.db')
        if not os.path.isfile(options.datafile):
            print 'You are missing the default GCMT database file %s. Run the convertdb.py script to retrieve it.' % options.datafile
            sys.exit(0)
        
    if not os.path.isfile(options.datafile):
        print 'Could not find the user-supplied database file %s. Run the convertdb.py script to create it from your text data file.' % options.datafile
        sys.exit(0)

    if len(args) == 1:
        args = args[0].split()
    if len(args) < 3:
        print 'Could not parse input arguments %s.  If you have a negative longitude or latitude, enclose all arguments in quotes.'
        parser.print_help()
        sys.exit(0)
        
    lat = float(args[0])
    lon = float(args[1])
    depth = float(args[2])
    magnitude = float(args[3])
    if len(args) == 5:
        etime = datetime.datetime.strptime(args[4],'%Y%m%d%H%M')
    else:
        etime = None
    gs = GMPESelector('zoneconfig2.ini',options.datafile)

    gmpe,fmstring,regdict,trdict,plungevals,slabvals,eqdict,warning,mtsource = gs.selectGMPE(lat,lon,depth,magnitude,date=etime)

    if not options.outputCsv:
        print 'GMPE: %s' % gmpe
        print 'Focal Mechanism: %s' % fmstring
        print 'FE Region Number: %i' % regdict['number']
        print 'Tectonic Regime: %s' % trdict['name']
        print 'Focal Mechanism:'
        if plungevals is None:
            print 'No Focal Mechanism determined'
        else:
            tensordict = {'gcmt':'Global Centroid Moment Tensor',
                          'wphase':'USGS W-Phase Moment Tensor',
                          'usgs':'USGS Centroid Moment Tensor',
                          'body':'USGS Body Wave Moment Tensor',
                          'region':'USGS/SLU Regional Moment Tensor',
                          'historical':'Historical solution',
                          'composite':'Composite solution'}
            print '\tT Axis Strike and Plunge: %.2f %.2f' % (plungevals['T']['azimuth'],plungevals['T']['plunge'])
            print '\tP Axis Strike and Plunge: %.2f %.2f' % (plungevals['P']['azimuth'],plungevals['P']['plunge'])
            print '\tN Axis Strike and Plunge: %.2f %.2f' % (plungevals['N']['azimuth'],plungevals['N']['plunge'])
            fmt1 = '\tFirst Nodal Plane strike,dip,rake: %.2f %.2f %.2f'
            tpl1 = (plungevals['NP1']['strike'],plungevals['NP1']['dip'],plungevals['NP1']['rake'])
            print fmt1 % tpl1
            fmt2 = '\tSecond Nodal Plane strike,dip,rake: %.2f %.2f %.2f'
            tpl2 = (plungevals['NP2']['strike'],plungevals['NP2']['dip'],plungevals['NP2']['rake'])
            print fmt2 % tpl2
            print '\tMoment Source: %s' % tensordict[mtsource]
        print 'Slab Parameters:'
        print '\tStrike Dip Depth: %.2f %.2f %.2f' % (slabvals['strike'],slabvals['dip'],slabvals['depth'])
        print 'Eq2: %s' % eqdict['eq2']
        print 'Eq3a: %s' % eqdict['eq3a']
        print 'Eq3b: %s' % eqdict['eq3b']
        print 'Warning: %s' % warning
    else:
        if len(args) < 5:
            time = 'Unknown'
        else:
            time = args[4]
        fmt = '%s,%.4f,%.4f,%.1f,%.1f, %s,%s,"%s",%i, %.1f,%.1f,%.1f,%.1f,%.1f,%.1f, %.1f,%.1f,%.1f,%.1f,%.1f,%.1f, %.1f,%.1f,%.1f  ,%s,%s,%s,"%s"'
        tp = plungevals['T']['plunge']
        ta = plungevals['T']['azimuth']
        np = plungevals['N']['plunge']
        na = plungevals['N']['azimuth']
        pp = plungevals['P']['plunge']
        pa = plungevals['P']['azimuth']
        np1s = plungevals['NP1']['strike']
        np1d = plungevals['NP1']['dip']
        np1r = plungevals['NP1']['rake']

        np2s = plungevals['NP2']['strike']
        np2d = plungevals['NP2']['dip']
        np2r = plungevals['NP2']['rake']

        slabstrike = slabvals['strike']
        slabdip = slabvals['dip']
        slabdepth = slabvals['depth']

        eq2 = eqdict['eq2']
        eq3a = eqdict['eq3a']
        eq3b = eqdict['eq3b']
        
        tpl = (time,lat,lon,depth,magnitude,
               gmpe,fmstring,regdict['name'].strip(),regdict['number'],
               ta,tp,na,np,pa,pp,
               np1s,np1d,np1r,np2s,np2d,np2r,slabstrike,slabdip,slabdepth,eq2,eq3a,eq3b,warning)
        print fmt % tpl
    
    
    
    
