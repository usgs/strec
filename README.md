[![Build Status](https: // travis - ci.org / usgs / strec.svg?branch=master)](https: // travis - ci.org / usgs / strec)
[![codecov](https: // codecov.io / gh / usgs / strec / branch / master / graph / badge.svg)](https: // codecov.io / gh / usgs / strec)


# SeismoTectonic Regime Earthquake Calculator (STREC)

This library and set of tools was created to provide functionality to
automatically determine the tectonic region of an earthquake
(Subduction, Active, Volcanic, Stable), and the distance to the tectonic
regions to which it does * not* belong.

In addition, STREC provides a tool that, in subduction zones, returns
information on the subducting interface, using the USGS Slab1.0 model
(https: // earthquake.usgs.gov / data / slab / models.php).

# GLOSSARY

In STREC we define a number of terms that may not be commonly
understood, so they are explained here.  These terms may be different
from the Garcia paper upon which this software is originally based.

    - *Tectonic Region * : One of Subduction, Active, Volcanic, or Stable.
        We have split up the globe into these four regions, such that any
        point on the globe should fall into one and only one of these
        regions.

            * *Subduction * : A tectonic region defined by one plate descending below
            another(e.g., the western portion of the United States).

            * *Active * : A tectonic region which experiences crustal deformation due
            to plate tectonics.

            * *Volcanic * : A tectonic region which is dominated by volcanic
            activity.  This also includes what are referred to as "hot spots".

            * *Stable * : Tectonic regions which unlike Active regions, do not
            experience crustal deformation(e.g., the interior of the
                                           Australian continent.)

    - *Tectonic Domain * : This is a sub-grouping of tectonic regions, such
        that individual polygons in any of the Tectonic Regions above will
        have one of the following for the Tectonic Domain attribute:

            * *SCR (generic) * : Generic Stable Continental Region
            * *SCR (above slab) * : Stable Continental Region, above slab.
            * *ACR (shallow) * : Active Crustal Region, shallow.
            * *ACR (deep) * : Active Crustal Region, deep.
            * *ACR (oceanic boundary) * : Active Crustal Region, at oceanic boundary.
            * *ACR (hot spot) * : Active Crustal Region, at hot spot.
            * *SZ (generic) * : Generic Subduction Zone.
            * *SZ (outer - trench) * : Subduction Zone on the outer trench.
            * *SZ (on - shore) * : Subduction Zone, on-shore.
            * *SZ (inland / back - arc) * : Subduction Zone, inland or on back-arc.
            * *SOR (generic) *: Generic Stable Oceanic Region.
            * *SOR (above slab) * : Stable Oceanic Region, above slab.
            * *ACR shallow (above slab) * : Shallow Active Crustal Region, above slab.
            * *ACR deep (above slab) * : Deep Active Crustal Region, above slab.
            * *ACR oceanic boundary (above slab) * : Oceanic Boundary Active Crustal Region, above slab.

    - *Tectonic Sub - Domain * : A domain sub-classification that varies with
        depth. This value will be one of:
            * *SCR * : Stable Continental Region.
            * *ACR * : Active Crustal Region.
            * *SZINtra * : Subduction Zone IntraSlab (below subduction interface).
            * *SZInter * : Subduction Zone Interface (on subduction interface).
            * *Volcanic * : In volcanic substrate.

    - *Oceanic * : Another region, not exclusive with the four Tectonic
        Regions, that indicates whether the point supplied is in the ocean
        (i.e., not continental).

    - *Continental * : The opposite of Oceanic.

    - *Focal Mechanism * : A set of parameters that define the deformation in
        the source region that generates the seismic waves of an earthquake.

    - *Tensor Type * : The short name for the algorithm used to generate
        the moment tensor used to determine focal mechanism, Kagan angle,
        etc.  This is usually a short code like * Mww * (W - phase), *Mwr*
        (regional), *Mwb * (body wave), or *composite *, which indicates that
        there is no computed moment tensor, so a composite of historical
        moment tensors around the input coordinates is used instead.

    - *Tensor Source * : When available, this is usually the network that
        contributed the moment tensor, followed by the ID used by that
        network(e.g., us_2000bmcg).

    - *Kagan Angle * : An single angle between any two moment tensors or in
        our case, between a moment tensor and a subducting slab.

    - *Composite Variability * : When the moment tensor solution is of type
    *composite * , a scalar value describing the variability of the moment
    tensors used to determine the composite.

    - *Distance to [Region] * : The great circle distance from the input
        coordinates to the nearest vertex of[Region] polygon.

    - *Domain Depth Band (1, 2 or 3) *: The default depth ranges, in the
        absence of subduction information, that can be used to determine the
        tectonic subtype within the defined depth range.

    - *Slab Model Region * : We currently use Slab 1.0 subduction models
        (Hayes 2012), which are currently provided for 13 regions around
        the globe.  These regions are described in detail here:
        https: // earthquake.usgs.gov / data / slab / models.php

    - *Slab Model Depth * : The best estimate of depth to subduction
        interface.

    - *Slab Model Depth Uncertainty * : The best estimate of the uncertainty
        of the depth to subduction interface.

    - *Slab Model Dip * : The best estimate of the dip angle of the
        subducting plate.

    - *Slab Model Strike * : The best estimate of the strike angle of the
        subducting plate.

    - *Is Like Interface * : A boolean indicating whether the moment tensor
        strike angle is similar to the slab strike(Garcia 2012).

    - *Is Near Interface * : A boolean indicating whether the earthquake
        depth is within a threshold distance from the slab depth.

    - *Is In Slab * : A boolean indicating whether the earthquake
        depth is below a threshold distance from the slab depth.

# INSTALLATION


Currently, the easiest way to install STREC is to use the install script found in this repository.

# Pre-requisites

    - You should be comfortable using a terminal window in general, and
        the bash shell in particular.

    - You should have either Anaconda

        https: // www.anaconda.com / download/

        or Miniconda

        https: // conda.io / miniconda.html

        installed on your system.  In theory, this code should work on
        Windows, but has not been tested on that platform.

    - You should have git installed on your system.  On Linux or Mac OS,
        you can determine this by typing:

        `which git`

        If you see a response that indicates you have git installed on your
        system (something like * /usr / bin / git *), then you are set.  If not,
        install git by using the package manager for your system(Linux) or
        visiting this page:

        https: // git - scm.com / download

# Installing STREC In a New Conda Environment

    - Download the STREC source code by running the following command:

        `git clone https: // github.com / usgs / strec.git`

        This will create a directory called * strec * below your current working directory.

    - Run the installer script by typing:

        `cd strec
        bash installer.sh`

    - *Activate * the STREC virtual environment by running this command:

        `source activate strecenv`.

        You will need to add this command to your bash profile file(~ / .bash_profile or ~ / .bashrc),
        or re - run the command when you open a new terminal window.

# Installing STREC in an Existing Conda Environment

    Make sure you have the following dependencies already installed through conda or pip:
        - numpy
        - scipy
        - pyproj
        - pandas
        - openpyxl
        - xlrd
        - xlwt
        - pytest
        - pytest - cov
        - fiona
        - h5py
        - shapely
        - obspy
        - rasterio
        - gdal

Then run the following commands:

- `pip - q install https: // github.com / usgs / MapIO / archive / master.zip`
- `pip - q install https: // github.com / usgs / libcomcat / archive / master.zip`
- `pip - q install https: // github.com / usgs / earthquake - impact - utils / archive / master.zip`
- `pip - q install https: // github.com / usgs / strec / archive / master.zip`

# Using STREC

# Region Selector

    There are two tools provided by STREC that allow slightly different
    functionality.  If you are * not* interested in details about
    subduction zone interfaces, then you will want to use the * regselect*
    command.  This command can be used in a single event mode:

    - `regselect - e LAT LON DEPTH` to return information about an event based on hypocenter.
    - `regselect - d EVENTID` to return information about an event based on ComCat event ID.

ComCat event IDs can be obtained from ComCat event page url's. For example, for the url:

https: // earthquake.usgs.gov / earthquakes / eventpage / us2000bmcg

The event ID would be * us2000bmcg * .

The output of regselect should look something like this:
<pre >
For event located at - 23.4733, 135.3516, 0.0:
    TectonicRegion: Stable
    TectonicDomain: SCR(generic)
    DistanceToStable: 0.0
    DistanceToActive: 2372.34536692
    DistanceToSubduction: 1339.17982347
    DistanceToVolcanic: 1611.06881631
    Oceanic: False
    DistanceToOceanic: 2372.34536692
    DistanceToContinental: 0.0
    TectonicSubtype: SCR
    RegionContainsBackArc: False
    DomainDepthBand1: 50
    DomainDepthBand1Subtype: SCR
    DomainDepthBand2: 999
    DomainDepthBand2Subtype: SCR
    DomainDepthBand3: 1000
    DomainDepthBand3Subtype: SCR
< / pre >

Descriptions of the return fields can be found in the glossary above.

regselect can be used in batch mode, operating on input CSV or Excel files.

The NEIC * libcomcat * library and tools are installed along with STREC,
so you can use the * getcsv * command to generate input files to use
with regselect.  For example:

`getcsv ~ / big_events_2016.xlsx - s 2016 - 01 - 01 - e 2016 - 12 - 31T23: 59: 59 - m
6.5 9.9 - f excel`

will download basic event information for all magnitude 6.5 and
greater events in 2016.  This output can be directly piped into
regselect, and the results saved back out to Excel:

`regselect - i ~ / big_events_2016.xlsx - f excel - o ~ / regselect_events.xlsx`

# Subduction Selector

If you * are * interested in information about subduction zones(depth
                                                                to interface, etc.), then you will want to run the * subselect*
command.  Basic usage of * subselect * is the same as *regselect * :

    - `subselect - e LAT LON DEPTH` to return information about an event based on hypocenter.
    - `subselect - d EVENTID` to return information about an event based on ComCat event ID.

The output of subselect will look something like this:

<pre >
For event located at - 23.4733, 135.3516, 0.0:
    TectonicRegion: Stable
    TectonicDomain: SCR(generic)
    FocalMechanism: ALL
    TensorType: composite
    TensorSource: composite
    KaganAngle: nan
    CompositeVariability: nan
    NComposite: 0
    DistanceToStable: 0.0
    DistanceToActive: 2372.34536692
    DistanceToSubduction: 1339.17982347
    DistanceToVolcanic: 1611.06881631
    Oceanic: False
    DistanceToOceanic: 2372.34536692
    DistanceToContinental: 0.0
    TectonicSubtype: SCR
    RegionContainsBackArc: False
    DomainDepthBand1: 50
    DomainDepthBand1Subtype: SCR
    DomainDepthBand2: 999
    DomainDepthBand2Subtype: SCR
    DomainDepthBand3: 1000
    DomainDepthBand3Subtype: SCR
    SlabModelRegion:
    SlabModelType:
    SlabModelDepth: nan
    SlabModelDepthUncertainty: nan
    SlabModelDip: nan
    SlabModelStrike: nan
    IsLikeInterface: False
    IsNearInterface: False
    IsInSlab: False
< / pre >

subselect can also be used in batch mode, operating on input CSV or Excel files.

As above, getcsv output can be directly piped into
subselect, and the results saved back out to Excel:

`subselect - i ~ / big_events_2016.xlsx - f excel - o ~ / subselect_events.xlsx`

# Data Used in STREC

There are three datasets that are included with STREC:

    - Vector(GeoJSON format) data files that define the four mutually
        exclusive tectonic regions(Active, Stable, Volcanic, Subduction)
        and Oceanic.

- Database(SQLite format) of GCMT moment tensors that are used to
    determine composite moment tensors.  This can be overridden by the
    user(see below).

- USGS Slab 1.0 * subduction zone model grids(NetCDF4 / HDF5 COARDS
                                              format).  These models are described in detail on this page:
    https: // earthquake.usgs.gov / data / slab / models.php

The moment tensor database can be overridden by using the * strec_init*
command line tool(distributed with this repository), in one of two ways:

    - Downloading up - to - date versions of the GCMT moment tensors
    - Installing your own catalog of moment tensors.

To update to the most recent version of the GCMT moment tensors, do
the following:

`strec_init[DATAFOLDER]`

where[DATAFOLDER] is the location where you would like the new SQLite
database file to be located.  STREC programs will recognize that this
new file should override the data included in the repository by
looking at a config file that strec_init will create in
*~ / .strec / strec.ini * .

To use your own catalog of moment tensors, you must have a CSV or
Excel file of earthquake and moment tensor data, with the following
(exactly named) columns:

    - time(YYYY - MM - DD HH: MM: SS for CSV)
    - lat(decimal degrees)
    - lon(decimal degrees)
    - depth(km)
    - mag(moment magnitude units)
    - mrr(dyne - cm)
    - mtt(dyne - cm)
    - mpp(dyne - cm)
    - mrt(dyne - cm)
    - mrp(dyne - cm)
    - mtp(dyne - cm)

and then run the following command:

`strec_init - d[DATAFILE] - s[SOURCE]`

where[DATAFILE] is the name of the aforementioned CSV / Excel file and
[SOURCE] is the name of the originator of the moment tensor solutions
("gcmt", "us", "duputel", etc.)

As above, STREC will recognize this new data as the source of moment
tensors by looking in the STREC ini file.

* - At the time of this writing, an updated set of subduction models
    is in preparation, and will hopefully be added to the repository
    soon.
