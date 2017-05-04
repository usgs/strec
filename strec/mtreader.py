#!/usr/bin/env python

#stdlib imports
import re
import datetime
import pytz
import math
from xml.dom.minidom import parse
import os.path
import sqlite3
import urllib.request, urllib.parse, urllib.error,urllib.request,urllib.error,urllib.parse
import json
import sys
import copy

#local imports
from .cmt import compToAxes


class ReaderError(Exception):
    """Used to indicate errors in the reader classes."""

def appendDataFile(infile,dbfile,filetype,dtype,hasHeader=False):
    if filetype == 'ndk':
        reader = NDKReader(infile,dtype)
    elif filetype == 'xml':
        reader = NDKReader(infile,dtype)
    elif filetype == 'csv':
        reader = CSVReader(infile,dtype)
    else:
        return False
    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()
    keys = ['id','type','lat','lon','depth','mag',
        'mrr','mtt','mpp','mrt','mrp','mtp',
        'tplunge','tazimuth','nplunge','nazimuth','pplunge','pazimuth',
        'np1strike','np1dip','np1rake','np2strike','np2dip','np2rake']
    colstr = 'origin,fmtype,lat,lon,mag,depth,mrr,mtt,mpp,mrt,mrp,mtp,tplunge,tazimuth,nplunge,nazimuth,pplunge,pazimuth,np1strike, np1dip, np1rake, np2strike, np2dip,np2rake'
    for r in reader.generateRecords(hasHeader=hasHeader):
        fmtlist = []
        for key in keys:
            val = r[key]
            if isinstance(val,str) or isinstance(val,datetime.datetime):
                fmtlist.append('"%s"')
            else:
                fmtlist.append('%f')
        fmtstr = ','.join(fmtlist)
        querystr = 'INSERT INTO event (%s) VALUES (%s)' % (colstr,fmtstr)
        tpl = (r['id'],r['type'],r['lat'],r['lon'],r['depth'],r['mag'],
               r['mrr'],r['mtt'],r['mpp'],r['mrt'],r['mrp'],r['mtp'],
               r['tplunge'],r['tazimuth'],r['nplunge'],r['nazimuth'],r['pplunge'],r['pazimuth'],
               r['np1strike'],r['np1dip'],r['np1rake'],r['np2strike'],r['np2dip'],r['np2rake'])
        cursor.execute(querystr % tpl)
        conn.commit()

    cursor.close()
    conn.close()
    return True

def createDataFile(infile,dbfile,filetype,dtype,hasHeader=False):
    if filetype == 'ndk':
        reader = NDKReader(infile,dtype)
    elif filetype == 'xml':
        reader = NDKReader(infile,dtype)
    elif filetype == 'csv':
        reader = CSVReader(infile,dtype)
    else:
        return False
    if os.path.isfile(dbfile):
        os.remove(dbfile)
    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()
    create_query = '''CREATE TABLE event (origin DATETIME, fmtype TEXT, lat REAL, lon REAL, mag REAL, depth REAL,
    mrr REAL, mtt REAL, mpp REAL, mrt REAL, mrp REAL, mtp REAL,
    tplunge REAL, tazimuth REAL,
    nplunge REAL, nazimuth REAL,
    pplunge REAL, pazimuth REAL,
    np1strike REAL, np1dip REAL,np1rake REAL, np2strike REAL, np2dip REAL,np2rake REAL)
    '''
    cursor.execute(create_query)
    conn.commit()
    cursor.close()
    conn.close()
    appendDataFile(infile,dbfile,filetype,dtype,hasHeader=hasHeader)
    return True

class MTReader(object):
    fh = None
    def __init__(self,mtfile,type=None):
        self.mtfile = mtfile
        self.type = type
        
    def generateRecords(self,startDate=None,enddate=None,hasHeader=False):
        pass

class ComCatReader(MTReader):
    URLBASE = 'http://comcat.cr.usgs.gov/earthquakes/feed/search.php?%s'
    def __init__(self):
        pass

    def getEvents(self,pdict):
        params = urllib.parse.urlencode(pdict)
        searchurl = self.URLBASE % params
        datadict = None
        try:
            fh = urllib.request.urlopen(searchurl)
            data = fh.read()
            data2 = data[len(pdict['callback'])+1:-2]
            datadict = json.loads(data2)
            fh.close()
        except Exception as errorobj:
            raise errorobj
        return datadict['features']
            
    def generateRecords(self,startdate=None,enddate=None,hasHeader=False):
        utc = pytz.UTC
        if startdate is None:
            startdate = datetime.datetime(1971,1,1)
            startdate = utc.localize(startdate)
        if enddate is None:
            enddate = datetime.datetime(1971,1,1)
            enddate = utc.localize(enddate)
        if (enddate-startdate).days < 365:
            mintime = int(startdate.strftime('%s'))*1000
            maxtime = int(enddate.strftime('%s'))*1000
            params = pdict = {'productType[]':'moment-tensor,',
                              'minEventTime':mintime,
                              'maxEventTime':maxtime,
                              'callback':'comsearch'}
            events = self.getEvents(params)
        else:
            ndays = (enddate-startdate).days
            nyears = int(math.ceil(ndays/365.0))
            events = []
            mindate = startdate
            maxdate = mindate + datetime.timedelta(days=365)
            for i in range(0,nyears):
                mintime = int(mindate.strftime('%s'))*1000
                maxtime = int(maxdate.strftime('%s'))*1000
                params = pdict = {'productType[]':'moment-tensor,',
                                  'minEventTime':mintime,
                                  'maxEventTime':maxtime,
                                  'callback':'comsearch'}
                events = events + self.getEvents(params)
                mindate = maxdate
                maxdate = mindate + datetime.timedelta(days=365)
        for event in events:
            etimesecs = int(event['properties']['time'])/1000
            etime = datetime.datetime.utcfromtimestamp(etimesecs)
            if etime < startdate or etime > enddate:
                continue
            edicts = self.getMomentDicts(event)
            for edict in edicts:
                yield edict
                
    def getMomentDicts(self,event):
        eventdicts = []
        datadict = {}
        url = event['properties']['url'] + '.json'
        try:
            fh = urllib.request.urlopen(url)
            data = fh.read()
            datadict = json.loads(data)
            fh.close()
        except Exception as errorobj:
            raise errorobj
        eqtime = datadict['summary']['time']
        eqid = str(datetime.datetime.utcfromtimestamp(int(eqtime)/1000))
        lat = float(datadict['summary']['latitude'])
        lon = float(datadict['summary']['longitude'])
        depth = float(datadict['summary']['depth'])
        mag = float(datadict['summary']['magnitude'])
        for mt in datadict['products']['moment-tensor']:
            if mt['status'] == 'DELETE':
                continue
            bsource = mt['properties']['beachball-source']
            bcode = mt['code']
            #we have gcmt data going back further, directly from GCMT website
            if bsource == 'LD' and bcode.find('GCMT') > -1:
                continue
                
            mttype = mt['properties']['beachball-type']
            try:
                mrr = float(mt['properties']['tensor-mrr'])
                mtt = float(mt['properties']['tensor-mtt'])
                mpp = float(mt['properties']['tensor-mpp'])
                mrt = float(mt['properties']['tensor-mrt'])
                mrp = float(mt['properties']['tensor-mrp'])
                mtp = float(mt['properties']['tensor-mtp'])
            except:
                continue
            np1strike = float(mt['properties']['nodal-plane-1-strike'])
            np2strike = float(mt['properties']['nodal-plane-2-strike'])
            np1dip = float(mt['properties']['nodal-plane-1-dip'])
            np2dip = float(mt['properties']['nodal-plane-2-dip'])
            try:
                np1rake = float(mt['properties']['nodal-plane-1-rake'])
            except:
                np1rake = float(mt['properties']['nodal-plane-1-slip'])
            try:
                np2rake = float(mt['properties']['nodal-plane-2-rake'])
            except:
                np2rake = float(mt['properties']['nodal-plane-2-slip'])
            try:
                T,N,P,NP1,NP2 = compToAxes(mrr,mtt,mpp,mrt,mrp,mtp)
            except Exception as exc:
                pass
            tplunge = T['plunge']
            tazimuth = T['azimuth']
            nplunge = N['plunge']
            nazimuth = N['azimuth']
            pplunge = P['plunge']
            pazimuth = P['azimuth']
            eventdicts.append({'id':eqid,'type':mttype,
                               'lat':lat,'lon':lon,
                               'depth':depth,'mag':mag,
                               'mrr':mrr,'mtt':mtt,
                               'mpp':mpp,'mrt':mrt,
                               'mrp':mrp,'mtp':mtp,
                               'tplunge':tplunge,'tazimuth':tazimuth,
                               'nplunge':nplunge,'nazimuth':nazimuth,
                               'pplunge':pplunge,'pazimuth':pazimuth})
        return eventdicts
        
class CSVReader(MTReader):
    idfmtsec = '%Y%m%d%H%M%S'
    idfmtmin = '%Y%m%d%H%M'
    def generateRecords(self,startdate=None,enddate=None,hasHeader=False):
        if self.fh is None:
            self.fh = open(self.mtfile,'rt')
            if hasHeader:
                line = self.fh.readline() #read header row
        for line in self.fh.readlines():
            try:
                if startdate is not None and enddate is not None: 
                    parts = line.split(',')
                    tid = datetime.datetime.strptime(parts[0].strip(),self.idfmt)
                    if tid >= startdate and tid <= enddate:
                        yield self.readline(line)
                else:
                    yield self.readline(line)
            except Exception as msg:
                raise ReaderError('Error reading data from line:\n"%s".\nIs this a header row?' % line.strip())

        self.fh.close()

    def readline(self,line):
        record = {}
        parts = line.split(',')
        try:
            tstr = parts[0].strip()
            if len(tstr) == 12:
                record['id'] = datetime.datetime.strptime(tstr,self.idfmtmin)
            else:
                record['id'] = datetime.datetime.strptime(tstr,self.idfmtsec)
            record['type'] = self.type
            record['lat'] = float(parts[1].strip())
            record['lon'] = float(parts[2].strip())
            record['depth'] = float(parts[3].strip())
            record['mag'] = float(parts[4].strip())
            
            record['mrr'] = float(parts[5].strip())
            record['mtt'] = float(parts[6].strip())
            record['mpp'] = float(parts[7].strip())
            record['mrt'] = float(parts[8].strip())
            record['mrp'] = float(parts[9].strip())
            record['mtp'] = float(parts[10].strip())

            if len(parts) > 11:
                record['tazimuth'] = float(parts[11].strip())
                record['tplunge'] = float(parts[12].strip())
                record['nazimuth'] = float(parts[13].strip())
                record['nplunge'] = float(parts[14].strip())
                record['pazimuth'] = float(parts[15].strip())
                record['pplunge'] = float(parts[16].strip())

                record['np1strike'] = float(parts[17].strip())
                record['np1dip'] = float(parts[18].strip())
                record['np1rake'] = float(parts[19].strip())
                record['np2strike'] = float(parts[20].strip())
                record['np2dip'] = float(parts[21].strip())
                record['np2rake'] = float(parts[22].strip())
            else:
                #calculate these values using obspy code
                T,N,P,NP1,NP2 = compToAxes(record['mrr'],record['mtt'],record['mpp'],
                                           record['mrt'],record['mrp'],record['mtp'])
                record['tazimuth'] = T['azimuth']
                record['tplunge'] = T['plunge']
                record['nazimuth'] = N['azimuth']
                record['nplunge'] = N['plunge']
                record['pazimuth'] = P['azimuth']
                record['pplunge'] = P['plunge']

                record['np1strike'] = NP1['strike']
                record['np1dip'] = NP1['dip']
                record['np1rake'] = NP1['rake']
                record['np2strike'] = NP2['strike']
                record['np2dip'] = NP2['dip']
                record['np2rake'] = NP2['rake']
        except Exception as msg:
            raise Exception(msg)
        return record

class NDKReader(MTReader):
    def generateRecords(self,startdate=None,enddate=None,hasHeader=False):
        tdict = {}
        if self.fh is None:
            self.fh = open(self.mtfile,'rt')
        lc = 0
        for line in self.fh.readlines():
            if (lc+1) % 5 == 1:
                self.parseLine1(line,tdict)
                lc += 1
                continue
            if (lc+1) % 5 == 2:
                self.parseLine2(line,tdict)
                lc += 1
                continue
            if (lc+1) % 5 == 3:
                self.parseLine3(line,tdict)
                lc += 1
                continue
            if (lc+1) % 5 == 4:
                self.parseLine4(line,tdict)
                lc += 1
                continue
            if (lc+1) % 5 == 0:
                self.parseLine5(line,tdict)
                if startdate is not None and enddate is not None:
                    if tdict['eventTime'] >= startdate and tdict['eventTime'] <= enddate:
                        yield self.trimFields(tdict)
                else:
                    yield self.trimFields(tdict)
                lc += 1
                tdict = {}
        
        self.fh.close()
        
    def trimFields(self,tdict):
        record = {}
        record['id'] = tdict['eventTime']
        record['type'] = self.type
        record['lat'] = tdict['eventLatitude']
        record['lon'] = tdict['eventLongitude']
        record['depth'] = tdict['eventDepth']
        record['mag'] = tdict['momentMagnitude']
        record['tazimuth'] = tdict['eigenVectorAzimuths'][0]
        record['tplunge'] = tdict['eigenVectorPlunges'][0]
        record['nazimuth'] = tdict['eigenVectorAzimuths'][1]
        record['nplunge'] = tdict['eigenVectorPlunges'][1]
        record['pazimuth'] = tdict['eigenVectorAzimuths'][2]
        record['pplunge'] = tdict['eigenVectorPlunges'][2]
        record['np1strike'] = tdict['nodalPlane1Strike']
        record['np1dip'] = tdict['nodalPlane1Dip']
        record['np1rake'] = tdict['nodalPlane1Rake']
        record['np2strike'] = tdict['nodalPlane2Strike']
        record['np2dip'] = tdict['nodalPlane2Dip']
        record['np2rake'] = tdict['nodalPlane2Rake']
        record['mrr'] = tdict['tensorMrr']
        record['mpp'] = tdict['tensorMpp']
        record['mtt'] = tdict['tensorMtt']
        record['mtp'] = tdict['tensorMtp']
        record['mrp'] = tdict['tensorMrp']
        record['mrt'] = tdict['tensorMrt']
        return record

    def parseLine1(self,line,tdict):
        tdict['eventSource'] = line[0:4]
        dstr = line[5:26]
        year = int(dstr[0:4])
        month = int(dstr[5:7])
        day = int(dstr[8:10])
        hour = int(dstr[11:13])
        minute = int(dstr[14:16])
        fseconds = float(dstr[17:])
        seconds = int(fseconds)
        if seconds > 59: #
            seconds = 59
        microseconds = int((fseconds-seconds)*1e6)
        if microseconds > 999999:
            microseconds = 999999
        try:
            tdict['eventTime'] = datetime.datetime(year,month,day,hour,minute,seconds,microseconds)
        except:
            pass
        tdict['eventLatitude'] = float(line[27:33])
        tdict['eventLongitude'] = float(line[34:41])
        tdict['eventDepth'] = float(line[42:47])
        parts = line[48:55].split()
        mag1 = float(line[47:51])
        mag2 = float(line[51:55])
        tdict['eventMagnitudes'] = [mag1,mag2]
        tdict['eventLocation'] = line[56:80].strip()
    
    def parseLine2(self,line,tdict):
        tdict['eventID'] = line[0:16].strip()

        tdict['BodyWaveStations'] = int(line[19:22].strip())
        tdict['BodyWaveComponents'] = int(line[22:27].strip())
        tdict['BodyWaveShortestPeriod'] = float(line[27:31].strip())

        tdict['SurfaceWaveStations'] = int(line[34:37].strip())
        tdict['SurfaceWaveComponents'] = int(line[37:42].strip())
        tdict['SurfaceWaveShortestPeriod'] = float(line[42:46].strip())

        tdict['MantleWaveStations'] = int(line[49:52].strip())
        tdict['MantleWaveComponents'] = int(line[52:57].strip())
        tdict['MantleWaveShortestPeriod'] = float(line[57:61].strip())

        cmt = line[62:68].strip()
        m0 = re.search("CMT:\\s*0",cmt)
        m1 = re.search("CMT:\\s*1",cmt)
        m2 = re.search("CMT:\\s*2",cmt)

        if (m0 is not None):
            tdict['sourceInversionType'] = "general moment tensor"
        elif (m1 is not None):
            tdict['sourceInversionType'] = "standard moment tensor"
        elif (m2 is not None):
            tdict['sourceInversionType'] = "double couple source"
        else:
            tdict['sourceInversionType'] = "unknown source inversion"

        tdict['momentRateFunction'] = line[69:74]
        tdict['momentRateFunctionDuration'] = float(line[75:].strip())

    def parseLine3(self,line,tdict):
        centroid = line[9:59]
        parts = centroid.split()

        microseconds = float(line[9:18].strip())*1e6;
        tdict['derivedEventTime'] = tdict['eventTime']+datetime.timedelta(microseconds=microseconds)

        tdict['derivedEventTimeError'] = float(line[18:23])
        tdict['derivedEventLatitude'] = float(line[23:30])
        tdict['derivedEventLatitudeError'] = float(line[29:34])
        tdict['derivedEventLongitude'] = float(line[34:42])
        tdict['derivedEventLongitudeError'] = float(line[42:47])
        tdict['derivedEventDepth'] = float(line[47:53])
        tdict['derivedEventDepthError'] = float(line[53:58])
        tdict['derivedDepthType'] = line[58:61].strip()

    def parseLine4(self,line,tdict):
        tdict['exponent'] = float(line[0:2])
        tdict['tensorMrr'] = float(line[2:9])*math.pow(10.0,tdict['exponent'])
        tdict['tensorMrrError'] = float(line[9:15])*math.pow(10.0,tdict['exponent'])
        tdict['tensorMtt'] = float(line[15:22])*math.pow(10.0,tdict['exponent'])
        tdict['tensorMttError'] = float(line[22:28])*math.pow(10.0,tdict['exponent'])
        tdict['tensorMpp'] = float(line[28:35])*math.pow(10.0,tdict['exponent'])
        tdict['tensorMppError'] = float(line[35:41])*math.pow(10.0,tdict['exponent'])
        tdict['tensorMrt'] = float(line[41:48])*math.pow(10.0,tdict['exponent'])
        tdict['tensorMrtError'] = float(line[48:54])*math.pow(10.0,tdict['exponent'])
        tdict['tensorMrp'] = float(line[54:61])*math.pow(10.0,tdict['exponent'])
        tdict['tensorMrpError'] = float(line[61:67])*math.pow(10.0,tdict['exponent'])
        tdict['tensorMtp'] = float(line[67:74])*math.pow(10.0,tdict['exponent'])
        tdict['tensorMtpError'] = float(line[74:])*math.pow(10.0,tdict['exponent'])

    def parseLine5(self,line,tdict):
        tdict['programVersion'] = line[0:3].strip()
        tdict['eigenVectorValues'] = []
        tdict['eigenVectorPlunges'] = []
        tdict['eigenVectorAzimuths'] = []

        tdict['eigenVectorValues'].append(float(line[3:11])*math.pow(10.0,tdict['exponent']))
        tdict['eigenVectorPlunges'].append(float(line[11:14]))
        tdict['eigenVectorAzimuths'].append(float(line[14:18]))

        tdict['eigenVectorValues'].append(float(line[18:26])*math.pow(10.0,tdict['exponent']))
        tdict['eigenVectorPlunges'].append(float(line[26:29]))
        tdict['eigenVectorAzimuths'].append(float(line[29:33]))

        tdict['eigenVectorValues'].append(float(line[33:41])*math.pow(10.0,tdict['exponent']))
        tdict['eigenVectorPlunges'].append(float(line[41:44]))
        tdict['eigenVectorAzimuths'].append(float(line[44:48]))

        tdict['scalarMoment'] = float(line[49:56].strip())*math.pow(10.0,tdict['exponent'])
        tdict['momentMagnitude'] = ((2.0/3.0) * math.log10(tdict['scalarMoment'])) - 10.7

        tdict['nodalPlane1Strike'] = float(line[56:60])
        tdict['nodalPlane1Dip'] = float(line[60:63])
        tdict['nodalPlane1Rake'] = float(line[63:68])

        tdict['nodalPlane2Strike'] = float(line[68:72])
        tdict['nodalPlane2Dip'] = float(line[72:75])
        tdict['nodalPlane2Rake'] = float(line[75:])

class QuakeMLReader(MTReader):
    rdict = {}
    dom = None
    timeFormat = '%Y-%m-%dT%H:%M:%S.%f'
    def generateRecords(self,startdate=None,enddate=None):
        #Tried to implement this as a SAX parser, but couldn't figure out how to
        #make the content handler a generator function.  Failing over to minidom
        #- hopefully I won't run out of memory!
        if startdate is None:
            startdate = datetime.datetime(1000,1,1)
        if enddate is None:
            enddate = datetime.datetime(3000,1,1)
        if self.dom is None:
            self.dom = parse(self.mtfile)
            eventlist = self.dom.getElementsByTagName('event')
        for event in eventlist:
            origin = event.getElementsByTagName('origin')[0] #Just use the first origin
            timestr = origin.getElementsByTagName('time')[0].getElementsByTagName('value')[0].firstChild.data
            etime = datetime.datetime.strptime(timestr,self.timeFormat)
            if etime < startdate or etime > enddate:
                continue
            self.rdict = {}
            self.rdict['id'] = etime
            latstr = origin.getElementsByTagName('latitude')[0].getElementsByTagName('value')[0].firstChild.data
            self.rdict['lat'] = float(latstr)
            lonstr = origin.getElementsByTagName('longitude')[0].getElementsByTagName('value')[0].firstChild.data
            self.rdict['lon'] = float(lonstr)
            depstr = origin.getElementsByTagName('depth')[0].getElementsByTagName('value')[0].firstChild.data
            self.rdict['depth'] = float(depstr)
            mechanism = event.getElementsByTagName('focalMechanism')[0]
            np1 = mechanism.getElementsByTagName('nodalPlanes')[0].getElementsByTagName('nodalPlane1')[0]
            self.rdict['np1strike'] = float(np1.getElementsByTagName('strike')[0].getElementsByTagName('value')[0].firstChild.data)
            self.rdict['np1dip'] = float(np1.getElementsByTagName('dip')[0].getElementsByTagName('value')[0].firstChild.data)
            self.rdict['np1rake'] = float(np1.getElementsByTagName('rake')[0].getElementsByTagName('value')[0].firstChild.data)
            np2 = mechanism.getElementsByTagName('nodalPlanes')[0].getElementsByTagName('nodalPlane2')[0]
            self.rdict['np2strike'] = float(np2.getElementsByTagName('strike')[0].getElementsByTagName('value')[0].firstChild.data)
            self.rdict['np2dip'] = float(np2.getElementsByTagName('dip')[0].getElementsByTagName('value')[0].firstChild.data)
            self.rdict['np2rake'] = float(np2.getElementsByTagName('rake')[0].getElementsByTagName('value')[0].firstChild.data)
            taxis = mechanism.getElementsByTagName('principalAxes')[0].getElementsByTagName('tAxis')[0]
            self.rdict['tazimuth'] = float(taxis.getElementsByTagName('azimuth')[0].getElementsByTagName('value')[0].firstChild.data)
            self.rdict['tplunge'] = float(taxis.getElementsByTagName('plunge')[0].getElementsByTagName('value')[0].firstChild.data)
            naxis = mechanism.getElementsByTagName('principalAxes')[0].getElementsByTagName('nAxis')[0]
            self.rdict['nazimuth'] = float(naxis.getElementsByTagName('azimuth')[0].getElementsByTagName('value')[0].firstChild.data)
            self.rdict['nplunge'] = float(naxis.getElementsByTagName('plunge')[0].getElementsByTagName('value')[0].firstChild.data)
            paxis = mechanism.getElementsByTagName('principalAxes')[0].getElementsByTagName('pAxis')[0]
            self.rdict['pazimuth'] = float(paxis.getElementsByTagName('azimuth')[0].getElementsByTagName('value')[0].firstChild.data)
            self.rdict['pplunge'] = float(paxis.getElementsByTagName('plunge')[0].getElementsByTagName('value')[0].firstChild.data)
            tensor = event.getElementsByTagName('momentTensor')[0]
            moment = float(tensor.getElementsByTagName('scalarMoment')[0].getElementsByTagName('value')[0].firstChild.data)
            self.rdict['mag'] = ((2.0/3.0) * math.log10(moment)) - 10.7
            self.rdict['type'] = self.type

            #figure out where these come from in QuakeML later...
            self.rdict['mrr'] = 'NULL'
            self.rdict['mtt'] = 'NULL'
            self.rdict['mpp'] = 'NULL'
            self.rdict['mrt'] = 'NULL'
            self.rdict['mrp'] = 'NULL'
            self.rdict['mtp'] = 'NULL'
            yield self.rdict
        self.dom.unlink()
    
if __name__ == '__main__':
    #get a months worth of moment tensor records from ComCat
    comreader = ComCatReader()
    d1 = datetime.datetime(1976,1,1,0,0)
    #d2 = datetime.datetime.now()
    #d2 = datetime.datetime(2002,10,1)
    d2 = datetime.datetime.now()
    nc = 0
    for record in comreader.generateRecords(startdate=d1,enddate=d2):
        print('%s,%.1f,%s' % (record['id'],record['mag'],record['type']))
        sys.stdout.flush()
        nc += 1
    print('There are %i moment tensor records in ComCat' % nc)
    sys.exit(0)
    xreader = QuakeMLReader('xmlsample.xml',type='GCMT')
    for record in xreader.generateRecords():
        print('%s,%.1f,%s' % (record['id'],record['mag'],record['type']))
        
    creader = CSVReader('csvtest.csv','User')
    for record in creader.generateRecords():
        print(record['id'],record['mag'],record['type'])

    nreader = NDKReader('aug10.ndk','GCMT')
    for record in nreader.generateRecords():
        print(record['id'],record['mag'],record['type'])
