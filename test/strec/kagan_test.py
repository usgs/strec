#!/usr/bin/env python

import numpy as np
from strec.kagan import get_kagan_angle


def test_kagan_consistency():
    # from https://earthquake.usgs.gov/earthquakes/eventpage/us2000ar20#moment-tensor
    mww = (108, 47, -98)
    mwc = (111, 46, -94)
    mwb = (311, 47, -85)

    mww_mwc = get_kagan_angle(mww[0], mww[1], mww[2], mwc[0], mwc[1], mwc[2])
    mww_mwb = get_kagan_angle(mww[0], mww[1], mww[2], mwb[0], mwb[1], mwb[2])
    mwc_mwb = get_kagan_angle(mwc[0], mwc[1], mwc[2], mwb[0], mwb[1], mwb[2])

    np.testing.assert_almost_equal(mww_mwc, 3.07, decimal=1)
    np.testing.assert_almost_equal(mww_mwb, 14.43, decimal=1)
    np.testing.assert_almost_equal(mwc_mwb, 13.95, decimal=1)


def test_kagan_slab():
    events = {'Sumatra': (336, 7, 114),
              'Tohoku': (193, 9, 78),
              'Maule': (178, 77, 86),
              'Illapel': (353, 19, 83)}
    # TODO - get slab values for these events
    #tuple is depth,dip,strike
    slabs = {'Sumatra': (38.66, 20.45, 307.08),
             'Tohoku': (30.23, 14.89, 190.22),
             'Maule': (29.33, 19.64, 378.94),
             'Illapel': (29.09, 18.60, 364.10)}
    for eqname, eqparams in events.items():
        event_strike, event_dip, event_rake = eqparams
        slabparams = slabs[eqname]
        slab_depth, slab_dip, slab_strike = slabparams
        kagan = get_kagan_angle(event_strike, event_dip,
                                event_rake, slab_strike, slab_dip, 90)
        print('%s event: Kagan Angle %.2f' % (eqname, kagan))


if __name__ == '__main__':
    test_kagan_consistency()
    test_kagan_slab()
