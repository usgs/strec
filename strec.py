#!/usr/bin/env python

from optparse import OptionParser
import sys
import os.path
import ConfigParser
import getpass
import datetime

from strec.gmpe import GMPESelector
import strec.utils

if __name__ == '__main__':

    usage = """usage: %prog [options] -- lat lon depth magnitude [date]
    STREC - Seismo-Tectonic Regionalization of Earthquake Catalogs
    GCMT Composite Focal Mechanism Solution: %prog lat lon depth magnitude
    GCMT Historical or Composite Focal Mechanism Solution: %prog lat lon depth magnitude [date]
    User-defined, GCMT Historical, or GCMT Composite:%prog -d datafolder lat lon depth magnitude [date]

    NB: If you are specifying a negative latitude or longitude, you must add "--" at the
    end of the optional arguments so that the command line parser knows not to treat the
    negative sign as an optional argument.
    """
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--datafile",dest="datafile",
                      metavar="DATAFILE",
                      help="Specify the database (.db) file containing moment tensor solutions.")
    parser.add_option("-c", "--csv-out",
                      action="store_true", dest="outputCSV", default=False,
                      help="print output as csv")
    parser.add_option("-x", "--xml-out",
                      action="store_true", dest="outputXML", default=False,
                      help="print output as csv")
    parser.add_option("-p", "--pretty-out",
                      action="store_true", dest="outputPretty", default=False,
                      help="print output as human readable text")
    parser.add_option("-f", "--force-composite",
                      action="store_true", dest="forceComposite", default=False,
                      help="Force a composite solution, even if an exact historical moment tensor can be found.")


    (options, args) = parser.parse_args()

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

    if options.datafile is None:
        if not os.path.isfile(gcmtfile):
            fmt = 'You are missing the default GCMT database file %s. Run strec_init.py to retrieve it.'
            print fmt % gcmtfile
            sys.exit(0)
        datafile = gcmtfile
    else:
        datafile = options.datafile
        
    if not os.path.isfile(datafile):
        print 'Could not your file %s. You may need to run strec_convert.py first.' % datafile
        sys.exit(0)

    forceComposite = False
    lat = float(args[0])
    lon = float(args[1])
    depth = float(args[2])
    magnitude = float(args[3])
    if len(args) == 5:
        etime = datetime.datetime.strptime(args[4],'%Y%m%d%H%M')
    else:
        etime = None
        forceComposite = True

    if options.forceComposite:
        forceComposite = True

    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    zoneconfigfile = os.path.join(homedir,'strec.ini')
    gs = GMPESelector(zoneconfigfile,datafile,homedir,datafolder)

    strecresults = gs.selectGMPE(lat,lon,depth,magnitude,date=etime,forceComposite=forceComposite)
    
    if options.outputCSV:
        strecresults.renderCSV(sys.stdout)
    elif options.outputXML:
        strecresults.renderXML(sys.stdout)
    else:
        strecresults.renderPretty(sys.stdout)

