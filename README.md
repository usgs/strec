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








