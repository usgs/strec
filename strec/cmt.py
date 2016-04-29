#!/usr/bin/env python

import sqlite3
import datetime
import sys
import obspy.imaging.beachball
import math
from optparse import OptionParser 

def compToAxes(mrr,mtt,mpp,mrt,mrp,mtp):
    """
    Calculate Principal Axes and Nodal Planes from Moment Tensor components.
    Input: mrr,mtt,mpp,mrt,mrp,mtp
    Output: Tuple of Dictionaries:
    T: azimuth and plunge
    N: azimuth and plunge
    P: azimuth and plunge
    NP1: strike, dip, and rake
    NP2: strike, dip, and rake
    """
    mt = myMomentTensor(mtt,mtp,mrt,mpp,mrp,mrr)
    axes = obspy.imaging.beachball.mt2axes(mt) #T, N and P
    plane1 = obspy.imaging.beachball.mt2plane(mt)
    plane2 = obspy.imaging.beachball.aux_plane(plane1.strike,plane1.dip,plane1.rake)
    T = {'azimuth':axes[0].strike,'plunge':axes[0].dip}
    N = {'azimuth':axes[1].strike,'plunge':axes[1].dip}
    P = {'azimuth':axes[2].strike,'plunge':axes[2].dip}
    NP1 = {'strike':plane1.strike,'dip':plane1.dip,'rake':plane1.rake}
    NP2 = {'strike':plane2[0],'dip':plane2[1],'rake':plane2[2]}
    return (T,N,P,NP1,NP2)

def myMomentTensor(mtt,mtp,mrt,mpp,mrp,mrr):
    return obspy.imaging.beachball.MomentTensor(mrr,mtt,mpp,mrt,mrp,mtp,1)

def getCartDist(angle1,angle2):
    x1 = math.cos(math.radians(angle1))
    y1 = math.sin(math.radians(angle1))
    x2 = math.cos(math.radians(angle2))
    y2 = math.sin(math.radians(angle2))
    return math.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1))
    
def printEvent(edict):
    print '%-7s\t%-5s %-7s' % ('T Axis','Plunge','Azimuth')
    print '%-7s\t%-5.1f %-7.1f' % ('',edict['T']['plunge'],edict['T']['azimuth'])
    print '%-7s\t%-5s %-7s' % ('N Axis','Plunge','Azimuth')
    print '%-7s\t%-5.1f %-7.1f' % ('',edict['N']['plunge'],edict['N']['azimuth'])
    print '%-7s\t%-5s %-7s' % ('P Axis','Plunge','Azimuth')
    print '%-7s\t%-5.1f %-7.1f' % ('',edict['P']['plunge'],edict['P']['azimuth'])
    print
    print '%-7s\t%-6s %-7s %-7s' % ('NP 1','Strike','Dip','Rake')
    print '%-7s\t%-6.1f %-7.1f %-7.1f' % ('',edict['NP1']['strike'],edict['NP1']['dip'],edict['NP1']['rake'])
    print '%-7s\t%-6s %-7s %-7s' % ('NP 2','Strike','Dip','Rake')
    print '%-7s\t%-6.1f %-7.1f %-7.1f' % ('',edict['NP2']['strike'],edict['NP2']['dip'],edict['NP2']['rake'])
    print
    print 'Components:'
    print '\tMtt %g' % edict['Components']['mrr']
    print '\tMpp %g' % edict['Components']['mpp']
    print '\tMrr %g' % edict['Components']['mrr']
    print '\tMtp %g' % edict['Components']['mtp']
    print '\tMrt %g' % edict['Components']['mrt']
    print '\tMrp %g' % edict['Components']['mrp']

def getComposite(rows): #rows are: mrr,mtt,mpp,mrt,mrp,mtp
    m11 = 0.0
    m12 = 0.0
    m13 = 0.0
    m22 = 0.0
    m23 = 0.0
    m33 = 0.0
    for row in rows:
        trow = list(row[:])
        trow[5] = -trow[5]
        trow[4] = -trow[4]
        rmax = max(row)
        trow2 = [r/rmax for r in trow] #normalize all values by the maximum
        m11 += trow2[1]
        m12 += trow2[5]
        m13 += trow2[3]
        m22 += trow2[2]
        m23 += trow2[4]
        m33 += trow2[0]

    m11 /= len(rows)
    m12 /= len(rows)
    m13 /= len(rows)
    m22 /= len(rows)
    m23 /= len(rows)
    m33 /= len(rows)

    vm11 = 0.0
    vm12 = 0.0
    vm13 = 0.0
    vm22 = 0.0
    vm23 = 0.0
    vm33 = 0.0

    for row in rows:
        trow = list(row[:])
        trow[5] = -trow[5]
        trow[4] = -trow[4]
        rmax = max(row)
        trow2 = [r/rmax for r in trow] #normalize all values by the maximum
        vm11 = vm11 + ((trow2[1] - m11) * (trow2[1] - m11))
        vm12 = vm12 + ((trow2[5] - m12) * (trow2[5] - m12))
        vm13 = vm13 + ((trow2[3] - m13) * (trow2[3] - m13))
        vm22 = vm22 + ((trow2[2] - m22) * (trow2[2] - m22))
        vm23 = vm23 + ((trow2[4] - m23) * (trow2[4] - m23))
        vm33 = vm33 + ((trow2[0] - m33) * (trow2[0] - m33))

    vm11 - math.sqrt(vm11/len(rows))
    vm12 - math.sqrt(vm12/len(rows))
    vm13 - math.sqrt(vm13/len(rows))
    vm22 - math.sqrt(vm22/len(rows))
    vm23 - math.sqrt(vm23/len(rows))
    vm33 - math.sqrt(vm33/len(rows))
    varforbenius = vm11*vm11 + vm12*vm12 + vm13*vm13 + vm22*vm22 + vm23*vm23
    forbenius = m11*m11 + m12*m12 + m13*m13 + m22*m22 + m23*m23
    similarity = math.sqrt(varforbenius)/forbenius
    mt = myMomentTensor(m11,-m12,m13,m22,-m23,m33)
    axes = obspy.imaging.beachball.mt2axes(mt) #T, N and P
    plane1 = obspy.imaging.beachball.mt2plane(mt)
    plane2 = obspy.imaging.beachball.aux_plane(plane1.strike,plane1.dip,plane1.rake)
    compkeys = ['mrr','mtt','mpp','mrt','mtp','mrp']
    axkeys = ['value','plunge','azimuth']
    npkeys = ['strike','dip','rake']
    edict = dict(zip(compkeys,(m33,m11,m22,m13,-m23,-m12)))
    t = dict(zip(axkeys,(axes[0].val,axes[0].dip,axes[0].strike)))
    n = dict(zip(axkeys,(axes[1].val,axes[1].dip,axes[1].strike)))
    p = dict(zip(axkeys,(axes[2].val,axes[2].dip,axes[2].strike)))
    np1 = dict(zip(npkeys,(plane1.strike,plane1.dip,plane1.rake)))
    np2 = dict(zip(npkeys,(plane2[0],plane2[1],plane2[2])))
    edict.update(dict(zip(['T','N','P'],(t,n,p))))
    edict.update(dict(zip(['NP1','NP2'],(np1,np2))))
    return (edict,similarity,len(rows))

def getCompositeCMT(lat,lon,depth,dbfile,box=0.1,depthbox=10,nmin=3,maxbox=1.0,dbox=0.09):
    """
    Search a local sqlite gCMT database for a list of events near input event, calculate composite moment tensor.
    @param lat: Latitude (dd)
    @param lat: Longitude (dd)
    @param depth: Depth (km)
    @param dbfile: Path to sqlite database file
    @keyword box: half-width of latitude/longitude search box (dd)
    @keyword depthbox: half-width of depth search window (km)
    @keyword nmin: Minimum number of events to use to calculate composite moment tensor
    @keyword maxbox: Maximum size of search box (dd)
    @keyword dbox: Increment of search box (dd)
    """
    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()
    rows = []
    searchwidth = box
    while len(rows) < nmin and searchwidth < maxbox:
        qstr = 'SELECT mrr,mtt,mpp,mrt,mrp,mtp FROM event WHERE lat >= %.4f AND lat <= %.4f AND lon >= %.4f AND lon <= %.4f'
        query = qstr % (lat-searchwidth,lat+searchwidth,lon-searchwidth,lon+searchwidth)
        cursor.execute(query)
        rows = cursor.fetchall()
        if len(rows) >= nmin:
            break
        searchwidth += dbox

    if len(rows) < nmin:
        if len(rows) > 0:
            edict,similarity,nrows = getComposite(rows)
            return (edict,'Only %i events found for composite focal mechanism!' % len(rows))
        else:
            return (None,'No historical events found for composite focal mechanism!')

    edict,similarity,nrows = getComposite(rows)
    return (edict,'')

def getHistoricalCMT(time,dbfile,twindow=60):
    """
    Search a local sqlite gCMT database for a particular event specified by the user.
    @param lat: Latitude (dd)
    @param lat: Longitude (dd)
    @param depth: Depth (km)
    @param time: Origin time (datetime)
    @param dbfile: Path to sqlite database file
    @keyword depthbox: half-width of depth search distance (kilometers).
    @keyword minbox: Minimum spatial search width (decimal degrees).
    @keyword maxbox: Maximum spatial search width (decimal degrees).
    @keyword dbox:   Spatial search width increment (decimal degrees).
    @keyword twindow: half-width of time search window (seconds)
    """
    conn = sqlite3.connect(dbfile)
    timefmt = '%Y-%m-%d %H:%M:%S'
    cursor = conn.cursor()
    tmin = (time - datetime.timedelta(seconds=twindow)).strftime(timefmt)
    tmax = (time + datetime.timedelta(seconds=twindow)).strftime(timefmt)
    querystr = '''SELECT origin,lat,lon,depth,mag,
        mrr,mtt,mpp,mrt,mrp,mtp,
        tplunge,tazimuth,
        nplunge,nazimuth,
        pplunge,pazimuth,
        np1strike,np1dip,np1rake,np2strike,np2dip,np2rake
        FROM event WHERE origin >= "%s" AND origin <= "%s"''' % (tmin,tmax)
    cursor.execute(querystr)
    rows = cursor.fetchall()
    dtime = 1000000000
    itime = -1
    for i in range(0,len(rows)):
        etime = datetime.datetime.strptime(rows[i][0][0:19],'%Y-%m-%d %H:%M:%S')
        tdtime = abs((etime - time).seconds)
        if tdtime < dtime:
            dtime = tdtime
            itime = i
    if itime > -1:
        return (mapRow(rows[itime]),'')
    else:
        return (None,'')


def mapRow(row):
    edict = {}
    compkeys = ['mrr','mtt','mpp','mrt','mrp','mtp']
    axiskeys = ['plunge','azimuth']
    pkeys = ['strike','dip','rake']
    pl1keys = ['np1strike','np1dip','np1slip']
    pl2keys = ['np2strike','np2dip','np2slip']
    edict = dict(zip(compkeys,row[5:11]))
    T = dict(zip(axiskeys,row[11:13]))
    N = dict(zip(axiskeys,row[13:15]))
    P = dict(zip(axiskeys,row[15:17]))
    edict['T'] = T
    edict['N'] = N
    edict['P'] = P
    NP1 = dict(zip(pkeys,row[17:20]))
    NP2 = dict(zip(pkeys,row[20:23]))
    edict['NP1'] = NP1
    edict['NP2'] = NP2
    return edict

if __name__ == '__main__':
    usage = """usage: %prog [options]
    Composite: %prog -c -e 31.44,104.1,19.0 -f cmt.db
    Historical: %prog -i -e 31.44,104.1,19.0 -t 2008-05-12T06:28:01 -f cmt.db
    Test mode (compare obspy results with GCMT):%prog -a -f cmt.db
    """
    parser = OptionParser(usage=usage)
    parser.add_option("-i", "--historical",
                      action="store_true", dest="doHistorical", default=False,
                      help="Retrieve moment tensor from a historical event")
    parser.add_option("-c", "--composite",
                      action="store_true", dest="doComposite", default=False,
                      help="Retrieve composite moment tensor from a number of historical events")
    parser.add_option("-e", "--epicenter",dest="epicenter",
                      metavar="LAT,LON,DEPTH", help="Specify the epicenter (lat,lon,depth)")
    parser.add_option("-t", "--time",dest="time",
                      metavar="TIME", help="Specify the date/time (YYYY-MM-DDTHH:MM:SS")
    parser.add_option("-f", "--file",dest="file",
                      metavar="FILE", help="Specify the SQLite file containing earthquake data.")
    parser.add_option("-d", "--depthrange",default=10,dest="depthrange",
                      metavar="DEPTHRANGE", help="Specify the depth range +/- DEPTHRANGE km for search")
    parser.add_option("-s", "--searchmin",default=0.1,dest="searchmin",
                      metavar="SEARCHMIN", help="Specify the minimum horizontal search distance (dd)")
    parser.add_option("-m", "--searchmax",default=1.0,dest="searchmax",
                      metavar="SEARCHMAX", help="Specify the maximum horizontal search distance (dd)")
    parser.add_option("-k", "--searchint",default=0.09,dest="searchint",
                      metavar="SEARCHINT", help="Specify the horizontal search distance step (dd)")
    parser.add_option("-w", "--timewindow",default=60,dest="twindow",
                      metavar="TIMEWINDOW", help="Specify the time window +/- (sec)x")

    (options, args) = parser.parse_args()
    if (options.doHistorical and options.doComposite) or (not options.doHistorical and not options.doComposite):
        print 'You must select one of the modes "historical" or "composite".'
        parser.print_help()
        sys.exit(1)

    if options.doComposite:
        if options.time is not None:
            print 'Date/time not required for composite search.  Ignoring.'
        if options.epicenter is None:
            print 'Epicenter is required for composite search.'
            parser.print_help()
            sys.exit(1)

    if options.doHistorical:
        if options.time is None or options.epicenter is None:
            print 'Epicenter and time are required for a historical search.'
            parser.print_help()
            sys.exit(1)

    if options.file is None:
        print 'SQLite filename must be specified.'
        parser.print_help()
        sys.exit(1)

    dbfile = options.file

    #Attempt to parse the epicenter data
    lat = None
    lon = None
    depth = None
    try:
        lat,lon,depth = options.epicenter.split(',')
        lat = float(lat)
        lon = float(lon)
        depth = float(depth)
    except:
        print 'Could not parse lat,lon, depth from input: "%s"' % options.epicenter
        parser.print_help()
        sys.exit(1)

    #Attempt to parse the time
    time = None
    if options.time is not None:
        try:
            time = datetime.datetime.strptime(options.time,'%Y-%m-%dT%H:%M:%S')
        except:
            print 'Could not parse time from input: "%s"' % options.time
            parser.print_help()
            sys.exit(1)

    if options.doHistorical:
        edict = getHistoricalCMT(time,dbfile,twindow=options.twindow)
        if edict is not None:
            print 'Historical GCMT parameters:'
            printEvent(edict)

    if options.doComposite:
        edict,similar,nevents = getCompositeCMT(lat,lon,depth,dbfile,
                                                box=options.searchmin,depthbox=options.depthrange,
                                                maxbox=options.searchmax,dbox=options.searchint)
        if edict is not None:
            print 'Composite similarity is %f from %i events.' % (similar,nevents)
            print 'Composite GCMT parameters:'
            printEvent(edict)
            
