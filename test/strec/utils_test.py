#!/usr/bin/env python

from strec.utils import get_config

def test_get_config():
    config = get_config()

    if not isinstance(config,dict):
        dictionary = {}
        for section in config.sections():
            dictionary[section] = {}
            for option in config.options(section):
                dictionary[section][option] = config.get(section, option)
    else:
        dictionary = config.copy()
    
    assert sorted(list(dictionary.keys())) == ['CONSTANTS','DATA']
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
    assert sorted(cmp_options) == sorted(config['CONSTANTS'].keys())

if __name__ == '__main__':
    test_get_config()
