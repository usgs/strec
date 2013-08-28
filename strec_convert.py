#!/usr/bin/env python

import argparse
import sqlite3
import os.path
import sys
import datetime

from strec.mtreader import createDataFile,appendDataFile

usage = """Convert data from CSV, NDK, or QuakeML XML into internal database format (SQLite).
The default input format is CSV.
CSV format columns:
(Required)
1) Date/time (YYYYMMDDHHMMSS or YYYYMMDDHHMM)
2) Lat (dd)
3) Lon (dd)
4) Depth (km)
5) Mag
6) Mrr (dyne-cm)
7) Mtt (dyne-cm)
8) Mpp (dyne-cm)
9) Mrt (dyne-cm)
10) Mrp (dyne-cm)
11) Mtp (dyne-cm)
(Optional - if these are not supplied STREC will calculate them from moment tensor components above).
12) T Azimuth (deg)
13) T Plunge (deg)
14) N Azimuth (deg)
15) N Plunge (deg)
16) P Azimuth (deg)
17) P Plunge (deg)
18) NP1 Strike (deg)
19) NP1 Dip (deg)
20) NP1 Rake (deg)
21) NP2 Strike (deg)
22) NP2 Dip (deg)
23) NP2 Rake (deg)
"""
parser = argparse.ArgumentParser(description=usage,formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('infile')
parser.add_argument('outfile')
parser.add_argument("-n", "--ndk",
                  action="store_true", dest="usendk", default=False,
                  help="Input file is in NDK format")
parser.add_argument("-x", "--xml",
                  action="store_true", dest="usexml", default=False,
                  help="Input file is in QuakeML XML format")
parser.add_argument("-c", "--csv",
                  action="store_true", dest="usecsv", default=False,
                  help="Input file is in CSV format (Default)")
parser.add_argument("-s", "--skipfirst",
                  action="store_true", dest="hasheader", default=False,
                  help="CSV file has a header row which should be skipped")
parser.add_argument("-t", "--type",dest="fmtype",
                  metavar="TYPE", help="Specify the moment tensor type (cmt,body wave,etc.) Defaults to 'User'.")

args = parser.parse_args()
if not args.infile or not args.outfile:
    print 'Missing input and/or output files.'
    parser.print_help()
    sys.exit(0)

suminput = sum([options.usecsv,options.usexml,options.usendk])
    
if suminput > 1:
    print 'You must provide ONLY one of -n, -c, or -x options.'
    parser.print_usage()
    sys.exit(0)

infile = args.infile
outfile = args.outfile

if args.fmtype is None:
    args.fmtype = 'User'

if args.usendk:
    filetype = 'ndk'
if args.usecsv:
    filetype = 'csv'
if args.usexml:
    filetype = 'xml'

if os.path.isfile(outfile):
    print '%s already exists - appending new data.' % outfile
    try:
        appendDataFile(infile,outfile,filetype,args.fmtype,hasHeader=args.hasheader)
    except Exception,msg:
        print 'Error reading input file %s.\n%s' % (infile,msg)
        sys.exit(1)
else:
    try:
        createDataFile(infile,outfile,filetype,args.fmtype,hasHeader=args.hasheader)
    except Exception,msg:
        print 'Error reading input file %s.\n"%s"' % (infile,msg)
        sys.exit(1)
