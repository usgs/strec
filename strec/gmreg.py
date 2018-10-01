#!/usr/bin/env python

# stdlib imports
import os.path
from collections import OrderedDict

# third party
import numpy as np
import pandas as pd
from mapio.geodict import GeoDict
from mapio.reader import read

# local imports
from strec.utils import get_config

# As we add more layers, define their name/file mappings here.
# All of these files have polygons where the attribute is true.
TECTONIC_REGIONS = {1: 'DistanceToStable',
                    2: 'DistanceToActive',
                    3: 'DistanceToVolcanic',
                    4: 'DistanceToSubduction'}
OCEANIC_REGIONS = {1: 'DistanceToOceanic',
                   0: 'DistanceToContinental'}

DX = DY = 0.0083333333
XSPAN = YSPAN = 4.0

# for each of the above regions, when we're inside a polygon, we should
# capture the field below as the "Tectonic Domain".
DOMAIN_FIELD = 'REGIME_TYP'
SLABFIELD = 'SLABFLAG'
SCRFIELD = 'SCRFLAG'

# these are special layers (not exclusive with above regions)
# where are the areas of induced seismicity?
INDUCED = 'induced.json'
# where are the areas that are oceanic (i.e., not continental?)
OCEANIC = 'oceanic.json'

# this is a layer with many unassociated polygons that delineate purely geographic areas
# of seismic interest (usually areas which have a specific GMPE).
GEOGRAPHIC = 'geographic.json'

# for each of the above geographic regions, this is the attribute containing the name of the region
GEOGRAPHIC_FIELD = 'REG_NAME'


def geodetic_distance(lon1, lat1, lon2, lat2):
    distance = 6371.0 * \
        np.sqrt(((lon1 - lon2) * np.cos(0.5 * (lat1 + lat2)))
                ** 2 + (lat1 - lat2)**2)
    return distance


def get_dist_to_type(center_lon, center_lat, grid, regions):
    gd = grid.getGeoDict()
    #
    # The distance calculation wants everything in radians
    #
    lons = np.radians(np.linspace(gd.xmin, gd.xmax, gd.nx))
    lats = np.radians(np.linspace(gd.ymin, gd.ymax, gd.ny))
    mlons, mlats = np.meshgrid(lons, lats)

    center_lon_rad = np.radians(center_lon)
    center_lat_rad = np.radians(center_lat)

    #
    # The type at the epicenter is the type in the middle of the grid
    # (I'm not sure about the "- 1" part)
    #
    midx = int(gd.nx / 2 - 1)
    midy = int(gd.ny / 2 - 1)
    mytype = grid._data[midy, midx]
    #
    # Tectonic types are 1: stable, 2: active, 3: volcanic, 4: subduction
    # so iniitalize the zero element of the array NaN and the others Inf
    #
    distances = np.ones(len(regions))*np.inf
    dist_to_type = dict(zip(list(regions.values()), distances))
    tectype = regions[mytype]
    dist_to_type[tectype] = 0
    for tec_code in regions.keys():
        tectype = regions[tec_code]
        if tec_code == mytype:
            continue
        ixx = grid._data == tec_code
        if not np.any(ixx):
            continue
        tlons = mlons[ixx].flatten()
        tlats = mlats[ixx].flatten()
        dists = geodetic_distance(center_lon_rad,
                                  center_lat_rad,
                                  tlons, tlats)

        dist_to_type[tectype] = np.min(dists)
    return dist_to_type


class Regionalizer(object):
    def __init__(self, datafolder):
        """Determine tectonic region information given epicenter and depth.

        Args:
            datafolder (str): Path to directory containing spatial data
            for tectonic regions.
        """
        self._datafolder = datafolder
        self._tectonic_grid = os.path.join(datafolder, 'tectonic_global.grd')
        self._oceanic_grid = os.path.join(datafolder, 'oceanic_global.grd')

    @classmethod
    def load(cls):
        """Load regionalizer data from data in the repository.

        Returns:
            Regionalizer: Instance of Regionalizer class.
        """
        config = get_config()
        datadir = config['DATA']['folder']
        return cls(datadir)

    def getRegions(self, lat, lon, depth):
        """Get information about the tectonic region of a given hypocenter.

        Args:
            lat (float): Earthquake hypocentral latitude.
            lon (float): Earthquake hypocentral longitude.
            depth (float): Earthquake hypocentral depth.
        Returns:
            Series: Pandas series object containing labels:
                - TectonicRegion: Subduction, Active, Stable, or Volcanic.
                - DistanceToStable: Distance in km to nearest stable region.
                - DistanceToActive: Distance in km to nearest active region.
                - DistanceToSubduction: Distance in km to nearest subduction
                                        region.
                - DistanceToVolcanic: Distance in km to nearest volcanic
                                      region.
                - Oceanic: Boolean indicating if epicenter is in the ocean.
                - DistanceToOceanic: Distance in km to nearest oceanic region.
                - DistanceToContinental: Distance in km to nearest continental
                                         region.
        """
        regions = OrderedDict()

        gd = GeoDict.createDictFromCenter(lon, lat, DX, DY, XSPAN, YSPAN)

        tec_grid = read(self._tectonic_grid, samplegeodict=gd)
        region_dict = get_dist_to_type(lon, lat, tec_grid, TECTONIC_REGIONS)

        ocean_grid = read(self._oceanic_grid, samplegeodict=gd)
        ocean_dict = get_dist_to_type(lon, lat, ocean_grid, OCEANIC_REGIONS)

        if region_dict['DistanceToActive'] == 0:
            region_dict['TectonicRegion'] = 'Active'
        elif region_dict['DistanceToStable'] == 0:
            region_dict['TectonicRegion'] = 'Stable'
        elif region_dict['DistanceToSubduction'] == 0:
            region_dict['TectonicRegion'] = 'Subduction'
        else:
            region_dict['TectonicRegion'] = 'Volcanic'

        region_dict['DistanceToOceanic'] = ocean_dict['DistanceToOceanic']
        region_dict['DistanceToContinental'] = ocean_dict['DistanceToContinental']
        region_dict['Oceanic'] = False
        if ocean_dict['DistanceToOceanic'] == 0:
            region_dict['Oceanic'] = True

        regions = pd.Series(region_dict, index=['TectonicRegion',
                                                'DistanceToStable',
                                                'DistanceToActive',
                                                'DistanceToSubduction',
                                                'DistanceToVolcanic',
                                                'Oceanic',
                                                'DistanceToOceanic',
                                                'DistanceToContinental'])

        return regions
