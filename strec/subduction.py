def normAngle(angle):
    if angle > 360:
        angle = angle-360
    if angle < 0:
        angle = angle+360
    return angle


class SubductionZone(object):
    def __init__(self,slab_params,tensor_params,depth,config):
        """Check where in the subduction zone this event is (crust, interface, slab).

        :param slab_params:
          Dictionary containing depth, strike and dip of the slab interface at a given location.
        :param tensor_params:
          Dictionary containing the moment tensor parameters (six components, and nodal plane values.)
        :param depth:
          Event depth.
        :param config:
          dict containing keys:
          DSTRIKE_INTERF - ??
          DDIP_INTERF - ??
          DLAMBDA - ??
          DDEPTH_INTERF - Acceptable depth range around interface depth for interface event.
          DDEPTH_INTRA - intra-slab depth range.
        """
        self._dstrike = config['constants']['dstrike_interf']
        self._ddip = config['constants']['ddip_interf']
        self._dlambda = config['constants']['dlambda']
        self._ddepth_interface = config['constants']['ddepth_interf']
        self._ddepth_intraslab = config['constants']['ddepth_intra']
        self._slab_params = slab_params.copy()
        self._tensor_params = tensor_params.copy()
        self._depth = depth

    def checkRupturePlane(self):
        """Implement equation two from the paper.
        :return:
           
        """
        a = self._tensor_params['P']['azimuth']
        b1 = (normAngle((self._slab_params['strike']))-self._dstrike)
        b2 = (normAngle((self._slab_params['strike']))+self._dstrike)
        b3 = (normAngle((self._slab_params['strike']))-self._dstrike)
        b4 = (normAngle((self._slab_params['strike']))+self._dstrike)

        if a > 270 and b1 < 90:
            b1 = b1 + 360
        if a > 270 and b2 < 90:
            b2 = b2 + 360
        if a > 270 and b3 < 90:
            b3 = b3 + 360
        if a > 270 and b4 < 90:
            b4 = b4 + 360

        if a < 90 and b1 > 270:
            b1 = b1 - 360
        if a < 90 and b2 > 270:
            b2 = b2 - 360
        if a < 90 and b3 > 270:
            b3 = b3 - 360
        if a < 90 and b4 > 270:
            b4 = b4 - 360

        c1 = a >= b1
        c2 = a <= b2
        c3 = a >= b3
        c4 = a <= b4
    
        m2a = (c1 and c2 ) or (c3 and c4)
        m2b = ((self._tensor_params['P']['plunge'] >= self._slab_params['dip']-self._ddip) and \
               (self._tensor_params['P']['plunge'] <= self._slab_params['dip']+self._ddip))
        m2c1 = ((self._tensor_params['NP1']['rake'] > 90-self._dlambda) and \
                (self._tensor_params['NP1']['rake'] < 90+self._dlambda))
        m2c2 = ((self._tensor_params['NP2']['rake'] > 90-self._dlambda) and \
                (self._tensor_params['NP2']['rake'] < 90+self._dlambda))
        if (m2a and m2b and (m2c1 or m2c2)):
            return True
        else:
            return False

    def checkInterfaceDepth(self):
        #Check to see if the focal depth is within range of the slab depth
        c1 = self._depth >= self._slab_params['depth']-self._ddepth_interface
        c2 = self._depth < self._slab_params['depth']+self._ddepth_interface
        if (c1 and c2):
            return True
        else:
            return False

    def checkSlabDepth(self,intraslabdepth):
        """
        Check to see if the depth is deeper than the slab.

        :param slabdepth:
          
        @return: True if depth is deeper than the slab, False if not.
        """
        c1 = self._depth >= self._slab_params['depth']-self._ddepth_intraslab
        c2 = self._depth >= intraslabdepth
        if c1 and c2:
            return True
        else:
            return False
        
