#!/usr/bin/env python

from strec.utils import get_config

def test_get_config():
    config,config_file = get_config()
    assert config.sections() == ['CONSTANTS', 'DATA']
    cmp_options = ['maxradial_disthist',
                   'ddepth_intra',
                   'depth_rangecomp',
                   'ddepth_interf',
                   'maxradial_distcomp',
                   'dstrike_interf',
                   'minradial_distcomp',
                   'default_szdip',
                   'dlambda',
                   'minno_comp',
                   'step_distcomp',
                   'minradial_disthist',
                   'ddip_interf']
    assert cmp_options == config.options('CONSTANTS')

if __name__ == '__main__':
    test_get_config()
