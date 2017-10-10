#!/usr/bin/env python

from strec.utils import get_config

def test_get_config():
    config,config_file = get_config()
    assert config.sections() == ['REGIMES', 'FILES', 'CONSTANTS', 'DATA']
    cmp_options = ['minradial_disthist', 'maxradial_disthist',
                   'step_disthist', 'time_threshist',
                   'depth_rangehist', 'minradial_distcomp',
                   'maxradial_distcomp', 'step_distcomp',
                   'depth_rangecomp', 'minno_comp',
                   'default_szdip', 'scr_regime1',
                   'scr_regime2', 'scr_dist',
                   'sz_regime1', 'sz_regime2', 'sz_regimeout',
                   'sz_regimeback', 'acr_regimeshallow',
                   'tplunge_rs', 'bplunge_ds', 'bplunge_ss',
                   'pplunge_nm', 'delplunge_ss', 'dstrike_interf',
                   'ddip_interf', 'dlambda', 'ddepth_interf',
                   'ddepth_intra']
    assert cmp_options == config.options('CONSTANTS')

if __name__ == '__main__':
    test_get_config()
