<center>SeismoTectonic Regime Earthquake Calculator (STREC)</center>
=====

 This library and set of tools was created to provide functionality to
 determine automatically type of an earthquake (subduction zone
 interface, active crustal shallow, stable continental region, etc.),
 as well as the focal mechanism.

TOOLS
=====

There are three tools that come with STREC:

- getstrec.py - Determine the best seismo-tectonic regime and focal mechanism for an input earthquake.
- strec_convert.py - Convert data from CSV, NDK, or QuakeML XML into internal database format (SQLite).
- strec_init.py - Initialize STREC data directory with USGS NEIC Slab data and (optionally) GCMT data.

INSTALLATION
============

STREC has the following dependencies:
- Python 2.7+ (not 3.X!)
- numpy 1.5+
- scipy 0.10+
- matplotlib 1.3.0+
- pytz 2011n+

AND 

- obspy 0.8.2+

The best way to install the first set of these dependencies is to use one of the Python distributions described here:

<a href="http://www.scipy.org/install.html">http://www.scipy.org/install.html</a>

Anaconda and Enthought distributions have been successfully tested with strec.

Most of those distributions should include <em>pip</em>, a command line tool for installing and 
managing Python packages.  You will use pip to install obspy and STREC itself.  
 
You may need to open a new terminal window to ensure that the newly installed versions of python and pip
are in your path.

<em>NB: The Pyzo distribution installs Python 3.3, which is incompatible with the 2.x Python
code in STREC.</em>

Final dependencies
------------------
Once you have a Python distribution installed (Canopy, Anaconda, etc.), you will need to install 
obspy.  The best way to do this is using <b>pip</b>.  pip comes bundled with Anaconda and pythonxy, 
but may need an extra step on Canopy.

From the command line, type:
<pre>
[sudo] easy_install pip
</pre>

(sudo may be necessary, depending on whether you have permissions to install software with your regular account, and how Python has been installed).

To install obspy with pip:
<pre>
[sudo] pip install obspy
</pre>

Installing STREC
----------------

To install this package:

pip install git+git://github.com/usgs/strec.git

The last command will install strec_init.py, strec_convert.py, and getstrec.py in your path.  

Uninstalling and Updating
-------------------------

To uninstall:

pip uninstall strec

To update:

pip install -U git+git://github.com/usgs/strec.git

Usage
=====

To begin using STREC, you will need to first download some binary data that is not included with the source code.

<pre>
strec_init.py --help
usage: strec_init.py [-h] [-g] [-c] [-n] [-r] [-u]

Initialize STREC data directory with USGS NEIC Slab data and (optionally) GCMT data.

optional arguments:
  -h, --help    show this help message and exit
  -g, --gcmt    Download all GCMT moment tensor data
  -c, --comcat  Download all USGS ComCat moment tensor data (sans GCMT)
  -n, --noslab  Do NOT download slab data
  -r, --reinit  Re-initialize STREC application.
  -u, --update  Update gcmt data.
</pre>

Most users will want to download the GCMT data - this is used to populate a database used to determine the earthquake's focal 
mechanism based on historical seismicity.

<pre>
getstrec.py --help
usage: getstrec.py [-h] [-d DATAFILE] [-r PLOTFILE] [-a ANGLES] [-c] [-x] [-p]
                   [-f]
                   [LAT LON DEPTH MAG [DATE] [LAT LON DEPTH MAG [DATE] ...]]

Determine most likely seismo-tectonic regime of given earthquake.
    STREC - Seismo-Tectonic Regionalization of Earthquake Catalogs
    GCMT Composite Focal Mechanism Solution: %prog lat lon depth magnitude
    GCMT Historical or Composite Focal Mechanism Solution: %prog lat lon depth magnitude [date]
    User-defined, GCMT Historical, or GCMT Composite:%prog -d datafolder lat lon depth magnitude [date]
    

positional arguments:
  LAT LON DEPTH MAG [DATE]
                        lat,lon,depth,magnitude and optionally date/time (YYYYMMDDHHMM) of earthquake

optional arguments:
  -h, --help            show this help message and exit
  -d DATAFILE, --datafile DATAFILE
                        Specify the database (.db) file containing moment tensor solutions.
  -r PLOTFILE, --regionplot PLOTFILE
                        Tell STREC to plot the EQ location inside Flinn-Engdahl polygon, and provide the output filename.
  -a ANGLES, --angles ANGLES
                        Specify the focal mechanism by providing "strike dip rake"
  -c, --csv-out         print output as csv
  -x, --xml-out         print output as csv
  -p, --pretty-out      print output as human readable text
  -f, --force-composite
                        Force a composite solution, even if an exact historical moment tensor can be found.
</pre>

Sample:
<pre>
>>getstrec.py -29.97226 -71.343155 10.0 7.4

Returns the following output:

Time: Unknown
Lat: -29.97226
Lon: -71.343155
Depth: 10.0
Magnitude: 7.4
Earthquake Type: ACRsh
Focal Mechanism: RS
FE Region Name:  NEAR COAST OF CENTRAL CHILE
FE Region Number: 135
FE Seismotectonic Domain: SZ (generic)
Focal Mechanism:
	T Axis Strike and Plunge: 124.99 58.86
	P Axis Strike and Plunge: 282.13 29.11
	N Axis Strike and Plunge: 17.83 10.11
	First Nodal Plane strike,dip,rake: 345.28 18.35 56.09
	Second Nodal Plane strike,dip,rake: 200.59 74.86 100.48
	Moment Source: composite
Slab Parameters:
	Strike Dip Depth: 278.74 20.90 42.20
Focal mechanism satisfies interface conditions: True
Depth within interface depth interval: False
Depth within intraslab depth interval: False
Warning: 
</pre>

Users who have their own catalog of moment tensor solutions may wish to use them with STREC instead of the GCMT database.  
To convert these data into a form suitable for STREC, use strec_convert.py:

<pre>
strec_convert.py --help
usage: strec_convert.py [-h] [-n] [-x] [-c] [-s] [-t TYPE] infile outfile

Convert data from CSV, NDK, or QuakeML XML into internal database format (SQLite).
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

positional arguments:
  infile
  outfile

optional arguments:
  -h, --help            show this help message and exit
  -n, --ndk             Input file is in NDK format
  -x, --xml             Input file is in QuakeML XML format
  -c, --csv             Input file is in CSV format (Default)
  -s, --skipfirst       CSV file has a header row which should be skipped
  -t TYPE, --type TYPE  Specify the moment tensor type (cmt,body wave,etc.) Defaults to 'User'.
</pre>









