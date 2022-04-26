def norm_angle(angle):
    """Normalize input angle to be between 0-360 degrees.

    Args:
        angle (float): Angle in degrees.
    Returns:
        float: Input angle normalized to between 0-360 degrees.
    """
    return angle % 360


class SubductionZone(object):
    def __init__(self, slab_params, tensor_params, depth, config):
        """Check where in the subduction zone this event is (crust, interface, slab).

        Args:
        slab_params (dict): Dictionary containing depth, strike and dip of
            the slab interface at a given location.
        tensor_params (dict): Dictionary containing the moment tensor
            parameters (six components, and nodal plane values.)
        depth (float): Event depth.
        config (dict): dict containing keys:
            DSTRIKE_INTERF - Threshold strike angle difference.
            DDIP_INTERF - Threshold dip angle difference.
            DLAMBDA - Threshold rake angle difference.
            DDEPTH_INTERF - Acceptable depth range around interface depth for interface
            event.
            DDEPTH_INTRA - intra-slab depth range.
        """
        self._dstrike = float(config['CONSTANTS']['dstrike_interf'])
        self._ddip = float(config['CONSTANTS']['ddip_interf'])
        self._dlambda = float(config['CONSTANTS']['dlambda'])
        self._ddepth_interface = float(config['CONSTANTS']['ddepth_interf'])
        self._ddepth_intraslab = float(config['CONSTANTS']['ddepth_intra'])
        self._slab_params = slab_params.copy()
        if isinstance(tensor_params, dict):
            self._tensor_params = tensor_params.copy()
        else:
            self._tensor_params = None
        self._depth = depth

    def checkRupturePlane(self):
        """Compare moment tensor angles to slab angles, return True if similar.


        Returns:
            bool: Boolean value indicating if moment tensor is similar to slab.
        """
        if self._tensor_params is None:
            return False
        strike = self._slab_params['strike'] - 90
        a = self._tensor_params['P']['azimuth']
        b1 = (norm_angle(strike) - self._dstrike)
        b2 = (norm_angle(strike) + self._dstrike)
        b3 = (norm_angle(strike) - self._dstrike)
        b4 = (norm_angle(strike) + self._dstrike)

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

        m2a = (c1 and c2) or (c3 and c4)
        m2b = ((self._tensor_params['P']['plunge'] >= self._slab_params['dip'] -
                self._ddip) and
               (self._tensor_params['P']['plunge'] <= self._slab_params['dip'] +
               self._ddip))
        m2c1 = ((self._tensor_params['NP1']['rake'] > 90 - self._dlambda) and
                (self._tensor_params['NP1']['rake'] < 90 + self._dlambda))
        m2c2 = ((self._tensor_params['NP2']['rake'] > 90 - self._dlambda) and
                (self._tensor_params['NP2']['rake'] < 90 + self._dlambda))
        if (m2a and m2b and (m2c1 or m2c2)):
            return True
        else:
            return False

    def checkInterfaceDepth(self):
        """Check to see if the focal depth is within range of the slab depth.

        Returns:
            bool: True if event is close to slab interface depth, False otherwise.
        """
        c1 = self._depth >= self._slab_params['depth'] - self._ddepth_interface
        c2 = self._depth < self._slab_params['depth'] + self._ddepth_interface
        if (c1 and c2):
            return True
        else:
            return False

    def checkSlabDepth(self, intraslabdepth):
        """Check to see if the depth is deeper than the interface.

        Args:
            intraslabdepth (float): Upper limit of intraslab events.

        @return: True if depth is deeper than the slab, False if not.
        """
        c1 = self._depth >= self._slab_params['depth'] - self._ddepth_intraslab
        c2 = self._depth >= intraslabdepth
        if c1 and c2:
            return True
        else:
            return False
