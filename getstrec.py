#!/usr/bin/env python

import argparse
import sys
import os.path
import ConfigParser
import getpass
import datetime
import math

from strec.gmpe import GMPESelector
import strec.utils
from strec import cmt

def getPlungeValues(strike,dip,rake,mag):
    mom = 10**((mag*1.5)+16.1)
    d2r = math.pi/180.0
    
    mrr=mom*math.sin(2*dip*d2r)*math.sin(rake*d2r)
    mtt=-mom*((math.sin(dip*d2r)*math.cos(rake*d2r)*math.sin(2*strike*d2r))+(math.sin(2*dip*d2r)*math.sin(rake*d2r)*(math.sin(strike*d2r)*math.sin(strike*d2r))))
    mpp=mom*((math.sin(dip*d2r)*math.cos(rake*d2r)*math.sin(2*strike*d2r))-(math.sin(2*dip*d2r)*math.sin(rake*d2r)*(math.cos(strike*d2r)*math.cos(strike*d2r))))
    mrt=-mom*((math.cos(dip*d2r)*math.cos(rake*d2r)*math.cos(strike*d2r))+(math.cos(2*dip*d2r)*math.sin(rake*d2r)*math.sin(strike*d2r)))
    mrp=mom*((math.cos(dip*d2r)*math.cos(rake*d2r)*math.sin(strike*d2r))-(math.cos(2*dip*d2r)*math.sin(rake*d2r)*math.cos(strike*d2r)))
    mtp=-mom*((math.sin(dip*d2r)*math.cos(rake*d2r)*math.cos(2*strike*d2r))+(0.5*math.sin(2*dip*d2r)*math.sin(rake*d2r)*math.sin(2*strike*d2r)))

    plungetuple = cmt.compToAxes(mrr,mtt,mpp,mrt,mrp,mtp)
    plungevals = {}
    plungevals['T'] = plungetuple[0].copy()
    plungevals['N'] = plungetuple[1].copy()
    plungevals['P'] = plungetuple[2].copy()
    plungevals['NP1'] = plungetuple[3].copy()
    plungevals['NP2'] = plungetuple[4].copy()
    return plungevals

def processDate(datestr):
    etime = datetime.datetime.strptime(args[4],'%Y%m%d%H%M')
    return etime

if __name__ == '__main__':
    usage = """Determine most likely seismo-tectonic regime of given earthquake.
    STREC - Seismo-Tectonic Regionalization of Earthquake Catalogs
    GCMT Composite Focal Mechanism Solution: %prog lat lon depth magnitude
    GCMT Historical or Composite Focal Mechanism Solution: %prog lat lon depth magnitude [date]
    User-defined, GCMT Historical, or GCMT Composite:%prog -d datafolder lat lon depth magnitude [date]
    """
    parser = argparse.ArgumentParser(description=usage,formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("eqinfo", nargs='*',metavar='LAT LON DEPTH MAG [DATE]',
                        help='lat,lon,depth,magnitude and optionally date/time (YYYYMMDDHHMM) of earthquake')
    parser.add_argument("-d", "--datafile",dest="datafile",
                      metavar="DATAFILE",
                      help="Specify the database (.db) file containing moment tensor solutions.")
    parser.add_argument("-a", "--angles",dest="angles",
                      metavar="ANGLES",
                      help='Specify the focal mechanism by providing "strike dip rake"')
    parser.add_argument("-c", "--csv-out",
                      action="store_true", dest="outputCSV", default=False,
                      help="print output as csv")
    parser.add_argument("-x", "--xml-out",
                      action="store_true", dest="outputXML", default=False,
                      help="print output as csv")
    parser.add_argument("-p", "--pretty-out",
                      action="store_true", dest="outputPretty", default=False,
                      help="print output as human readable text")
    parser.add_argument("-f", "--force-composite",
                      action="store_true", dest="forceComposite", default=False,
                      help="Force a composite solution, even if an exact historical moment tensor can be found.")


    args = parser.parse_args()

    if len(args.eqinfo) < 4:
        parser.print_help()
        sys.exit(0)
    
    #Get the user parameters config object (should be stored in ~/.strec/strec.ini)
    try:
        config,configfile = strec.utils.getConfig()
    except Exception,msg:
        print msg
        sys.exit(1)

    if config is None:
        print 'Could not find a configuration file.  Run strec_init.py to create it.'
        sys.exit(0)
        
    datafolder = config.get('DATA','folder')
    gcmtfile = os.path.join(datafolder,strec.utils.GCMT_OUTPUT)

    if args.datafile is None:
        if not os.path.isfile(gcmtfile):
            fmt = 'You are missing the default GCMT database file %s. Run strec_init.py to retrieve it.'
            print fmt % gcmtfile
            sys.exit(0)
        datafile = gcmtfile
    else:
        datafile = args.datafile
        
    if not os.path.isfile(datafile):
        print 'Could not your file %s. You may need to run strec_convert.py first.' % datafile
        sys.exit(0)

    forceComposite = False
    lat = float(args.eqinfo[0])
    lon = float(args.eqinfo[1])
    depth = float(args.eqinfo[2])
    magnitude = float(args.eqinfo[3])
    if len(args.eqinfo) == 5:
        etime = datetime.datetime.strptime(args.eqinfo[4],'%Y%m%d%H%M')
    else:
        etime = None
        forceComposite = True

    if args.angles is not None:
        parts = args.angles.split()
        try:
            strike = float(parts[0])
            dip = float(parts[1])
            rake = float(parts[2])
            plungevals = getPlungeValues(strike,dip,rake,magnitude)
        except:
            print 'Could not parse Strike, Dip and Rake from "%s"' % args.angles
            sys.exit(1)
    else:
        plungevals = None
        
    if args.forceComposite:
        forceComposite = True
        plungevals = None

    gs = GMPESelector(configfile,datafile,datafolder)

    strecresults = gs.selectGMPE(lat,lon,depth,magnitude,date=etime,
                                 forceComposite=forceComposite,
                                 plungevals=plungevals)
    
    if args.outputCSV:
        strecresults.renderCSV(sys.stdout)
    elif args.outputXML:
        strecresults.renderXML(sys.stdout)
    else:
        strecresults.renderPretty(sys.stdout)

