#!/usr/bin/env python

#stdlib imports
import sqlite3
import datetime
import sys
import obspy.imaging.beachball
import math
from optparse import OptionParser

#third party imports
import numpy as np

#local imports
from .tensor import fill_tensor_from_components


def getComposite(rows):
    """rows is a list of tuples consisting of mrr,mtt,mpp,mrt,mrp,mtp

    """
    components = np.array(rows)
    components[:,4] *= -1
    components[:,5] *= -1
    nrows,ncols = components.shape
    #get max value in each row and tile to shape nrowsxncols
    max_values = np.tile(np.reshape(components.max(axis=1),(nrows,1)),ncols) 
    comp_norm = components / max_values
    comp_av = np.mean(comp_norm,axis=0)
    comp_av_tile = np.tile(np.reshape(comp_av,(ncols,1)),nrows).transpose()
    comp_sq = np.power((comp_norm - comp_av_tile),2)
    comp_sq_mean_sq = np.sqrt(np.mean(comp_sq,axis=0))

    m33 = comp_av[0]
    m11 = comp_av[1]
    m22 = comp_av[2]
    m13 = comp_av[3]
    m23 = comp_av[4]
    m12 = comp_av[5]
    
    vm33 = comp_sq_mean_sq[0]
    vm11 = comp_sq_mean_sq[1]
    vm22 = comp_sq_mean_sq[2]
    vm13 = comp_sq_mean_sq[3]
    vm23 = comp_sq_mean_sq[4]
    vm12 = comp_sq_mean_sq[5]
    varforbenius = vm11*vm11 + vm12*vm12 + vm13*vm13 + vm22*vm22 + vm23*vm23
    forbenius = m11*m11 + m12*m12 + m13*m13 + m22*m22 + m23*m23
    similarity = np.sqrt(varforbenius)/forbenius

    mrr = m33
    mtt = m11
    mpp = m22
    mrt = m13
    mrp = -m23
    mtp = -m12
    
    tensor = fill_tensor_from_components(mrr,mtt,mpp,mrt,mrp,mtp)
    return (tensor,similarity,nrows)


def getCompositeCMT(lat,lon,depth,dbfile,box=0.1,depthbox=10,nmin=3,maxbox=1.0,dbox=0.09):
    """
    Search a local sqlite gCMT database for a list of events near input event, calculate composite moment tensor.
    @param lat: Latitude (dd)
    @param lat: Longitude (dd)
    @param depth: Depth (km)
    @param dbfile: Path to sqlite database file
    @keyword box: half-width of latitude/longitude search box (dd)
    @keyword depthbox: half-width of depth search window (km)
    @keyword nmin: Minimum number of events to use to calculate composite moment tensor
    @keyword maxbox: Maximum size of search box (dd)
    @keyword dbox: Increment of search box (dd)
    """
    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()
    rows = []
    searchwidth = box
    while len(rows) < nmin and searchwidth < maxbox:
        qstr = 'SELECT mrr,mtt,mpp,mrt,mrp,mtp FROM earthquake WHERE lat >= %.4f AND lat <= %.4f AND lon >= %.4f AND lon <= %.4f'
        query = qstr % (lat-searchwidth,lat+searchwidth,lon-searchwidth,lon+searchwidth)
        cursor.execute(query)
        rows = cursor.fetchall()
        if len(rows) >= nmin:
            break
        searchwidth += dbox

    if len(rows) == 0:
        if len(rows) > 0:
            edict,similarity,nrows = getComposite(rows)
            return (edict,similarity,nrows)
        else:
            return (None,np.nan,0)

    edict,similarity,nrows = getComposite(rows)
    
    return (edict,similarity,nrows)

            
