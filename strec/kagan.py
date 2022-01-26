#!/usr/bin/env python

# import standard libraries
import numpy as np
from copy import deepcopy

# local imports
from .tensor import plane_to_tensor


def get_kagan_angle(strike1, dip1, rake1, strike2, dip2, rake2):
    """Calculate the Kagan angle between two moment tensors defined by strike,dip and rake.

    Kagan, Y. "Simplified algorithms for calculating double-couple rotation", 
    Geophysical Journal, Volume 171, Issue 1, pp. 411-418.

    Args:
        strike1 (float): strike of slab or moment tensor
        dip1 (float): dip of slab or moment tensor
        rake1 (float): rake of slab or moment tensor
        strike2 (float): strike of slab or moment tensor
        dip2 (float): dip of slab or moment tensor
        rake2 (float): rake of slab or moment tensor
    Returns:
        float: Kagan angle between two moment tensors
    """
    # convert from strike, dip , rake to moment tensor
    tensor1 = plane_to_tensor(strike1, dip1, rake1)
    tensor2 = plane_to_tensor(strike2, dip2, rake2)

    kagan = calc_theta(tensor1, tensor2)

    return kagan


def calc_theta(vm1, vm2):
    """Calculate angle between two moment tensor matrices.

    Args:
        vm1 (ndarray): Moment Tensor matrix (see plane_to_tensor).
        vm2 (ndarray): Moment Tensor matrix (see plane_to_tensor).
    Returns:
        float: Kagan angle (degrees) between input moment tensors.
    """
    # calculate the eigenvectors of either moment tensor
    V1 = calc_eigenvec(vm1)
    V2 = calc_eigenvec(vm2)

    # find angle between rakes
    th = ang_from_R1R2(V1, V2)

    # calculate kagan angle and return
    for j in range(3):
        k = (j + 1) % 3
        V3 = deepcopy(V2)
        V3[:, j] = -V3[:, j]
        V3[:, k] = -V3[:, k]
        x = ang_from_R1R2(V1, V3)
        if x < th:
            th = x
    return th * 180. / np.pi


def calc_eigenvec(TM):
    """  Calculate eigenvector of moment tensor matrix.


    Args:  
        ndarray: moment tensor matrix (see plane_to_tensor)

    Returns:    
        ndarray: eigenvector representation of input moment tensor.
    """

    # calculate eigenvector
    V, S = np.linalg.eigh(TM)
    inds = np.argsort(V)
    S = S[:, inds]
    S[:, 2] = np.cross(S[:, 0], S[:, 1])
    return S


def ang_from_R1R2(R1, R2):
    """Calculate angle between two eigenvectors.

    Args:  
        R1 (ndarray): eigenvector of first moment tensor
        R2 (ndarray): eigenvector of second moment tensor
    Returns:    
        float: angle between eigenvectors 
    """
    
#    return np.arccos((np.trace(np.dot(R1, R2.transpose())) - 1.) / 2.)
    return np.arccos(np.clip((np.trace(np.dot(R1, R2.transpose())) - 1.) / 2.,-1,1))
