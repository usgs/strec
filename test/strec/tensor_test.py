#!/usr/bin/env python

from collections import OrderedDict
import numpy as np
from strec.tensor import fill_tensor_from_angles, fill_tensor_from_components, plane_to_tensor
import datetime


def test_tensor():
    # from https://earthquake.usgs.gov/earthquakes/eventpage/us2000ar20#moment-tensor
    event = OrderedDict([('id', 'us2000ar20'),
                         ('time', datetime.datetime(
                             2017, 9, 19, 18, 14, 38, 380000)),
                         ('location', '1km ESE of Ayutla, Mexico'),
                         ('latitude', 18.5462),
                         ('longitude', -98.4871),
                         ('depth', 51),
                         ('magnitude', 7.1),
                         ('magtype', 'mww'),
                         ('url',
                          'https://earthquake.usgs.gov/earthquakes/eventpage/us2000ar20'),
                         ('us_Mwb_mrr', -4.7728e+19),
                         ('us_Mwb_mtt', 3.3005e+19),
                         ('us_Mwb_mpp', 1.4723e+19),
                         ('us_Mwb_mrt', 1.481e+18),
                         ('us_Mwb_mrp', -4.319e+18),
                         ('us_Mwb_mtp', -3.305e+19),
                         ('us_Mwb_np1_strike', '123.35'),
                         ('us_Mwb_np1_dip', '43.08'),
                         ('us_Mwb_np1_rake', '-95.65'),
                         ('us_Mwb_np2_strike', '311.07'),
                         ('us_Mwb_np2_dip', '47.18'),
                         ('us_Mwb_np2_rake', '-84.74')])
    strike = float(event['us_Mwb_np1_strike'])
    dip = float(event['us_Mwb_np1_dip'])
    rake = float(event['us_Mwb_np1_rake'])
    mag = event['magnitude']

    comps = plane_to_tensor(strike, dip, rake, mag=mag)
    mrr = comps[0][0]
    mtt = comps[1][1]
    mpp = comps[2][2]
    mrt = comps[0][1]
    mrp = comps[2][0]
    mtp = comps[1][2]
    rtol = 0.5  # how should this be chosen?
    atol = 0.0
    np.testing.assert_allclose(mrr, event['us_Mwb_mrr'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(mtt, event['us_Mwb_mtt'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(mpp, event['us_Mwb_mpp'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(mrt, event['us_Mwb_mrt'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(mrp, event['us_Mwb_mrp'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(mtp, event['us_Mwb_mtp'], rtol=rtol, atol=atol)

    tensor_from_angles = fill_tensor_from_angles(
        strike, dip, rake, magnitude=mag)
    np.testing.assert_allclose(
        tensor_from_angles['mrr'], event['us_Mwb_mrr'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(
        tensor_from_angles['mtt'], event['us_Mwb_mtt'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(
        tensor_from_angles['mpp'], event['us_Mwb_mpp'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(
        tensor_from_angles['mrt'], event['us_Mwb_mrt'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(
        tensor_from_angles['mrp'], event['us_Mwb_mrp'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(
        tensor_from_angles['mtp'], event['us_Mwb_mtp'], rtol=rtol, atol=atol)

    try:
        np.testing.assert_allclose(
            strike, tensor_from_angles['NP1']['strike'], rtol=0.0001, atol=0)
        np.testing.assert_allclose(
            dip, tensor_from_angles['NP1']['dip'], rtol=0.0001, atol=0)
        np.testing.assert_allclose(
            rake, tensor_from_angles['NP1']['rake'], rtol=0.0001, atol=0)
    except AssertionError as ae:
        try:
            np.testing.assert_allclose(
                strike, tensor_from_angles['NP2']['strike'], rtol=0.0001, atol=0)
            np.testing.assert_allclose(
                dip, tensor_from_angles['NP2']['dip'], rtol=0.0001, atol=0)
            np.testing.assert_allclose(
                rake, tensor_from_angles['NP2']['rake'], rtol=0.0001, atol=0)
        except AssertionError as ae2:
            raise AssertionError('Nodal plane angles are off.')

    mrr = event['us_Mwb_mrr']
    mtt = event['us_Mwb_mtt']
    mpp = event['us_Mwb_mpp']
    mrt = event['us_Mwb_mrt']
    mrp = event['us_Mwb_mrp']
    mtp = event['us_Mwb_mtp']

    tensor_from_comps = fill_tensor_from_components(
        mrr, mtt, mpp, mrt, mrp, mtp)
    np.testing.assert_allclose(
        tensor_from_comps['mrr'], event['us_Mwb_mrr'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(
        tensor_from_comps['mtt'], event['us_Mwb_mtt'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(
        tensor_from_comps['mpp'], event['us_Mwb_mpp'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(
        tensor_from_comps['mrt'], event['us_Mwb_mrt'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(
        tensor_from_comps['mrp'], event['us_Mwb_mrp'], rtol=rtol, atol=atol)
    np.testing.assert_allclose(
        tensor_from_comps['mtp'], event['us_Mwb_mtp'], rtol=rtol, atol=atol)

    try:
        np.testing.assert_allclose(
            strike, tensor_from_comps['NP1']['strike'], rtol=0.0001, atol=0)
        np.testing.assert_allclose(
            dip, tensor_from_comps['NP1']['dip'], rtol=0.0001, atol=0)
        np.testing.assert_allclose(
            rake, tensor_from_comps['NP1']['rake'], rtol=0.0001, atol=0)
    except AssertionError as ae:
        try:
            np.testing.assert_allclose(
                strike, tensor_from_comps['NP2']['strike'], rtol=0.0001, atol=0)
            np.testing.assert_allclose(
                dip, tensor_from_comps['NP2']['dip'], rtol=0.0001, atol=0)
            np.testing.assert_allclose(
                rake, tensor_from_comps['NP2']['rake'], rtol=0.0001, atol=0)
        except AssertionError as ae2:
            raise AssertionError('Nodal plane angles are off.')


if __name__ == '__main__':
    test_tensor()
