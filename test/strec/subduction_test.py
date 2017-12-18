#!/usr/bin/env python

# stdlib imports
import os.path
import sys
import configparser

# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
repodir = os.path.abspath(os.path.join(homedir, '..', '..'))
# put this at the front of the system path, ignoring any installed version of the repo
sys.path.insert(0, repodir)

# local imports
from strec.subduction import SubductionZone, norm_angle

# third party imports
import numpy as np
import fiona
from shapely.geometry import shape as tshape


def test_norm_angle():
    angle1 = norm_angle(375)
    assert angle1 == 15
    angle2 = norm_angle(-15)
    assert angle2 == 345
    angle3 = norm_angle(725)
    assert angle3 == 5


def test_rupture_plane():
    config = {'CONSTANTS': {'dstrike_interf': 30,
                            'ddip_interf': 30,
                            'dlambda': 60,
                            'ddepth_interf': 20,
                            'ddepth_intra': 10}}
    # using slab information from tohoku epicenter
    # and MT info from duputel solution for tohoku
    slab_params = {'strike': 190.22474670410156,
                   'dip': 14.894770622253418,
                   'depth': 30.23206329345703}

    tensor_params = {'NP1': {'strike': 193, 'dip': 9, 'rake': 78},
                     'NP2': {'strike': 25, 'dip': 81, 'rake': 92},
                     'P': {'azimuth': 113, 'plunge': 36}}

    depth = 29.0
    subzone = SubductionZone(slab_params, tensor_params, depth, config)
    assert subzone.checkRupturePlane()

    # Bio-Bio, Chile
    slab_params = {'strike': 18.470233917236328,
                   'dip': 20.36998748779297,
                   'depth': 31.825963973999023}
    tensor_params = {'NP1': {'strike': 178, 'dip': 77, 'rake': 86},
                     'NP2': {'strike': 17, 'dip': 14, 'rake': 108},
                     'P': {'azimuth': 272, 'plunge': 32}}

    depth = 22.9
    subzone = SubductionZone(slab_params, tensor_params, depth, config)
    assert subzone.checkRupturePlane()

    # Sumatra
    slab_params = {'strike': 307.0806884765625,
                   'dip': 20.450008392333984,
                   'depth': 38.658607482910156}
    tensor_params = {'NP1': {'strike': 336, 'dip': 7, 'rake': 114},
                     'NP2': {'strike': 132, 'dip': 84, 'rake': 87},
                     'P': {'azimuth': 224, 'plunge': 39}}

    depth = 30.0
    subzone = SubductionZone(slab_params, tensor_params, depth, config)
    assert subzone.checkRupturePlane()

    # Sumatra, random moment tensor (should fail)
    slab_params = {'strike': 307.0806884765625,
                   'dip': 20.450008392333984,
                   'depth': 38.658607482910156}
    tensor_params = {'NP1': {'strike': 224, 'dip': 81, 'rake': -169},
                     'NP2': {'strike': 132, 'dip': 79, 'rake': -9},
                     'P': {'azimuth': 88, 'plunge': 14}}

    depth = 30.0
    subzone = SubductionZone(slab_params, tensor_params, depth, config)
    assert not subzone.checkRupturePlane()


def test_interface_depth():
    config = {'CONSTANTS': {'dstrike_interf': 30,
                            'ddip_interf': 30,
                            'dlambda': 60,
                            'ddepth_interf': 20,
                            'ddepth_intra': 10}}
    # using slab information from tohoku epicenter
    # and MT info from duputel solution for tohoku
    slab_params = {'strike': 190.22474670410156,
                   'dip': 14.894770622253418,
                   'depth': 30.23206329345703}

    tensor_params = {'NP1': {'strike': 193, 'dip': 9, 'rake': 78},
                     'NP2': {'strike': 25, 'dip': 81, 'rake': 92},
                     'P': {'azimuth': 113, 'plunge': 36}}

    depth = 29.0
    subzone = SubductionZone(slab_params, tensor_params, depth, config)
    assert subzone.checkInterfaceDepth()

    # go down in the slab
    depth = 150
    subzone = SubductionZone(slab_params, tensor_params, depth, config)
    assert not subzone.checkInterfaceDepth()


def test_slab_depth():
    config = {'CONSTANTS': {'dstrike_interf': 30,
                            'ddip_interf': 30,
                            'dlambda': 60,
                            'ddepth_interf': 20,
                            'ddepth_intra': 10}}
    # using slab information from tohoku epicenter
    # and MT info from duputel solution for tohoku
    slab_params = {'strike': 190.22474670410156,
                   'dip': 14.894770622253418,
                   'depth': 30.23206329345703}

    tensor_params = {'NP1': {'strike': 193, 'dip': 9, 'rake': 78},
                     'NP2': {'strike': 25, 'dip': 81, 'rake': 92},
                     'P': {'azimuth': 113, 'plunge': 36}}

    depth = 29.0
    subzone = SubductionZone(slab_params, tensor_params, depth, config)
    assert not subzone.checkSlabDepth(70.0)

    # go down in the slab
    depth = 150
    subzone = SubductionZone(slab_params, tensor_params, depth, config)
    assert subzone.checkSlabDepth(70.0)


if __name__ == '__main__':
    test_norm_angle()
    test_rupture_plane()
    test_interface_depth()
    test_slab_depth()
