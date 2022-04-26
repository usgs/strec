# third party imports
import numpy as np
from obspy.imaging.beachball import aux_plane, mt2axes, mt2plane, MomentTensor


def fill_tensor_from_angles(strike, dip, rake, magnitude=6.0, source='unknown',
                            mtype='unknown'):
    """Fill in moment tensor parameters from strike,dip, and rake.

    Args:
        strike (float): Strike from (assumed) first nodal plane (degrees).
        dip (float): Dip from (assumed) first nodal plane (degrees).
        rake (float): Rake from (assumed) first nodal plane (degrees).
        magnitude (float): Magnitude for moment tensor
            (not required if using moment tensor for angular comparisons.)
        source (str): Source (network, catalog) for input parameters.
        mtype (str): Focal mechanism or moment tensor type (Mww,Mwb,Mwc, etc.)
    Returns:
        dict: Fully descriptive moment tensor dictionary, including fields:
            - mrr,mtt,mpp,mrt,mrp,mtp Moment tensor components.
            - T T-axis values:
              - azimuth (degrees)
              - plunge (degrees)
            - N N-axis values:
              - azimuth (degrees)
              - plunge (degrees)
            - P P-axis values:
              - azimuth (degrees)
              - plunge (degrees)
            - NP1 First nodal plane values:
              - strike (degrees)
              - dip (degrees)
              - rake (degrees)
            - NP2 Second nodal plane values:
              - strike (degrees)
              - dip (degrees)
              - rake (degrees)
    """
    mt = plane_to_tensor(strike, dip, rake, mag=magnitude)
    return fill_tensor_from_components(mt[0][0], mt[1][1], mt[2][2],
                                       mt[1][0], mt[0][2], mt[1][2],
                                       source=source, mtype=mtype)


def fill_tensor_from_components(mrr, mtt, mpp, mrt, mrp, mtp, source='unknown',
                                mtype='unknown'):
    """Fill in moment tensor parameters from moment tensor components.

    Args:
        mrr (float): Moment tensor component
        mtt (float): Moment tensor component
        mpp (float): Moment tensor component
        mrt (float): Moment tensor component
        mrp (float): Moment tensor component
        mtp (float): Moment tensor component
        source (str): Source (network, catalog) for input parameters.
        mtype (str): Focal mechanism or moment tensor type (Mww,Mwb,Mwc, etc.)
    Returns:
        dict: Fully descriptive moment tensor dictionary, including fields:
            - mrr,mtt,mpp,mrt,mrp,mtp Moment tensor components.
            - T T-axis values:
              - azimuth (degrees)
              - plunge (degrees)
            - N N-axis values:
              - azimuth (degrees)
              - plunge (degrees)
            - P P-axis values:
              - azimuth (degrees)
              - plunge (degrees)
            - NP1 First nodal plane values:
              - strike (degrees)
              - dip (degrees)
              - rake (degrees)
            - NP2 Second nodal plane values:
              - strike (degrees)
              - dip (degrees)
              - rake (degrees)
    """
    tensor_params = {'mrr': mrr,
                     'mtt': mtt,
                     'mpp': mpp,
                     'mrt': mrt,
                     'mrp': mrp,
                     'mtp': mtp}
    tensor_params['source'] = source
    tensor_params['type'] = mtype
    mt = MomentTensor(mrr, mtt, mpp, mrt, mrp, mtp, 1)
    tnp1 = mt2plane(mt)
    np1 = {'strike': tnp1.strike,
           'dip': tnp1.dip,
           'rake': tnp1.rake}
    tensor_params['NP1'] = np1.copy()
    strike2, dip2, rake2 = aux_plane(np1['strike'], np1['dip'], np1['rake'])
    np2 = {'strike': strike2,
           'dip': dip2,
           'rake': rake2}
    tensor_params['NP2'] = np2.copy()
    T, N, P = mt2axes(mt)
    tensor_params['T'] = {'azimuth': T.strike,
                          'value': T.val,
                          'plunge': T.dip}
    tensor_params['N'] = {'azimuth': N.strike,
                          'value': N.val,
                          'plunge': N.dip}
    tensor_params['P'] = {'azimuth': P.strike,
                          'value': P.val,
                          'plunge': P.dip}

    return tensor_params


def plane_to_tensor(strike, dip, rake, mag=6.0):
    """Convert strike,dip,rake values to moment tensor parameters.

    Args:
        strike (float): Strike from (assumed) first nodal plane (degrees).
        dip (float): Dip from (assumed) first nodal plane (degrees).
        rake (float): Rake from (assumed) first nodal plane (degrees).
        magnitude (float): Magnitude for moment tensor
            (not required if using moment tensor for angular comparisons.)
    Returns:
        nparray: Tensor representation as 3x3 numpy matrix:
            [[mrr, mrt, mrp]
            [mrt, mtt, mtp]
            [mrp, mtp, mpp]]
    """
    # define degree-radian conversions
    d2r = np.pi / 180.0
    # get exponent and moment magnitude
    magpow = mag * 1.5 + 16.1
    mom = np.power(10, magpow)

    # get tensor components
    mrr = mom * np.sin(2 * dip * d2r) * np.sin(rake * d2r)
    mtt = -mom * ((np.sin(dip * d2r) * np.cos(rake * d2r) * np.sin(2 * strike * d2r)) +
                  (np.sin(2 * dip * d2r) * np.sin(rake * d2r) *
                  (np.sin(strike * d2r) * np.sin(strike * d2r))))
    mpp = mom * ((np.sin(dip * d2r) * np.cos(rake * d2r) * np.sin(2 * strike * d2r)) -
                 (np.sin(2 * dip * d2r) * np.sin(rake * d2r) *
                 (np.cos(strike * d2r) * np.cos(strike * d2r))))
    mrt = -mom * ((np.cos(dip * d2r) * np.cos(rake * d2r) * np.cos(strike * d2r)) +
                  (np.cos(2 * dip * d2r) * np.sin(rake * d2r) * np.sin(strike * d2r)))
    mrp = mom * ((np.cos(dip * d2r) * np.cos(rake * d2r) * np.sin(strike * d2r)) -
                 (np.cos(2 * dip * d2r) * np.sin(rake * d2r) * np.cos(strike * d2r)))
    mtp = -mom * ((np.sin(dip * d2r) * np.cos(rake * d2r) * np.cos(2 * strike * d2r)) +
                  (0.5 * np.sin(2 * dip * d2r) * np.sin(rake * d2r) *
                  np.sin(2 * strike * d2r)))

    mt_matrix = np.array([[mrr, mrt, mrp],
                          [mrt, mtt, mtp],
                          [mrp, mtp, mpp]])
    mt_matrix = mt_matrix * 1e-7  # convert from dyne-cm to N-m
    return mt_matrix
