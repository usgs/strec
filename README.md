STREC
=====

 STREC stands for SeismoTectonic Regime Earthquake Calculator. It’s purpose is to determine automatically the earthquake type (subduction zone interface, active crustal shallow, stable continental region, etc.) and the earthquake focal mechanism.

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
- obspy 0.8.2+
- pytz 2011n+

Depending on your platform, there are a number of different ways to install these dependencies.  
While it is impossible to document the process for every possible system, here are some of the 
common ones:

Windows
-------
There are (at least) three possibilities for Python distributions that include most of the dependencies listed above:
- pythonxy <a href="https://code.google.com/p/pythonxy/">https://code.google.com/p/pythonxy/</a>
- Continuum Anaconda <a href="https://store.continuum.io/cshop/anaconda/">https://store.continuum.io/cshop/anaconda/</a>
- Enthought Canopy <a href="https://www.enthought.com/products/canopy/">https://www.enthought.com/products/canopy/</a>

pythonxy may not include pytz, but this should be easily installable using pip (see instructions below).

None of these distributions include obspy, but again this should be installable with pip.

Mac OSX
-------
Both Anaconda and Canopy (see above) are also available for OSX.  obspy can be installed with pip.

Linux
-----
On Ubuntu, you should be able to follow the instructions found on the ObsPy website for 
<a href="https://github.com/obspy/obspy/wiki/Installation-on-Linux-via-Apt-Repository">Ubuntu-based systems</a>.

This <em>should</em> install numpy and scipy as well.

On Red Hat Enterprise Linux (RHEL) systems, by far the easiest path is to use Anaconda or Canopy (see above).

Final dependencies
------------------
Once you have a Python distribution installed (Canopy, Anaconda, etc.), you will likely still need to install 
obspy and possibly pytz.  The best way to do this is using <b>pip</b>.  pip comes bundled with Anaconda and pythonxy, 
but needs an extra step on Canopy.

From the command line, type:
     [sudo] easy_install pip

(sudo may be necessary, depending on whether you have permissions to install software with your regular account, and how Python has been installed).

To install obspy with pip:
   [sudo] pip install obspy

Installing STREC
----------------

Click on the <a href="https://github.com/usgs/strec/archive/master.zip">Download ZIP</a> button on the 
STREC github repository page and save the file.  For the purposes of this example, assume that location is "/home/username/strec-master.zip".
Unzip that file, which should create a directory called "/home/username/strec-master".

At the command line, do the following:
   cd /home/username/
   [sudo] pip install strec-master/

(The trailing slash is important - it tells pip that you want to install code in that directory, *not* to search the PyPI archives).

Usage
=====

To begin using STREC, you will need to first download some binary data that is not included with the source code.

>strec_init.py --help
>usage: strec_init.py [-h] [-g] [-c] [-n] [-r] [-u]
>   
>Initialize STREC data directory with USGS NEIC Slab data and (optionally) GCMT data.
>   
>optional arguments:
>  -h, --help    show this help message and exit
>  -g, --gcmt    Download all GCMT moment tensor data
>  -c, --comcat  Download all USGS ComCat moment tensor data (sans GCMT)
>  -n, --noslab  Do NOT download slab data
>  -r, --reinit  Re-initialize STREC application.
>  -u, --update  Update gcmt data.

Most users will want to download the GCMT data - this is used to populate a database used to determine the 
earthquake's focal mechanism based on historical seismicity.

>getstrec.py --help
>usage: getstrec.py [-h] [-d DATAFILE] [-a ANGLES] [-c] [-x] [-p] [-f]
>                   [LAT LON DEPTH MAG [DATE] [LAT LON DEPTH MAG [DATE] ...]]
>
>Determine most likely seismo-tectonic regime of given earthquake.
>    STREC - Seismo-Tectonic Regionalization of Earthquake Catalogs
>    GCMT Composite Focal Mechanism Solution: %prog lat lon depth magnitude
>    GCMT Historical or Composite Focal Mechanism Solution: %prog lat lon depth magnitude [date]
>    User-defined, GCMT Historical, or GCMT Composite:%prog -d datafolder lat lon depth magnitude [date]
>    
>
>positional arguments:
>  LAT LON DEPTH MAG [DATE]
>                        lat,lon,depth,magnitude and optionally date/time (YYYYMMDDHHMM) of earthquake
>
>optional arguments:
>  -h, --help            show this help message and exit
>  -d DATAFILE, --datafile DATAFILE
>                        Specify the database (.db) file containing moment tensor solutions.
>  -a ANGLES, --angles ANGLES
>                        Specify the focal mechanism by providing "strike dip rake"
>  -c, --csv-out         print output as csv
>  -x, --xml-out         print output as csv
>  -p, --pretty-out      print output as human readable text
>  -f, --force-composite










