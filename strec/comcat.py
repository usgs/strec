#stdlib imports
from urllib.request import urlopen
import json

EVENT_URL = 'https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=EVENTID&format=geojson'
class ComCat(object):
    def __init__(self):
        pass
    
    def getPreferredMomentTensor(self,eventid,jdict=None):
        if jdict is None:
            eurl = EVENT_URL.replace('EVENTID',eventid)
            fh = urlopen(eurl)
            data = fh.read().decode('utf-8')
            fh.close()
            jdict = json.loads(data)
        
        if 'moment-tensor' not in jdict['properties']['products']:
            return {} #??
        mtparams = jdict['properties']['products']['moment-tensor'][0]['properties']
        tensor_params = {}
        tensor_params['mtt'] = float(mtparams['tensor-mtt'])
        tensor_params['mpp'] = float(mtparams['tensor-mpp'])
        tensor_params['mrr'] = float(mtparams['tensor-mrr'])
        tensor_params['mtp'] = float(mtparams['tensor-mtp'])
        tensor_params['mrt'] = float(mtparams['tensor-mrt'])
        tensor_params['mrp'] = float(mtparams['tensor-mrp'])
        tensor_params['T'] = {'value':float(mtparams['t-axis-length']),
                              'plunge':float(mtparams['t-axis-plunge']),
                              'azimuth':float(mtparams['t-axis-azimuth'])}
        tensor_params['N'] = {'value':float(mtparams['n-axis-length']),
                              'plunge':float(mtparams['n-axis-plunge']),
                              'azimuth':float(mtparams['n-axis-azimuth'])}
        tensor_params['P'] = {'value':float(mtparams['p-axis-length']),
                              'plunge':float(mtparams['p-axis-plunge']),
                              'azimuth':float(mtparams['p-axis-azimuth'])}
        tensor_params['NP1'] = {'strike':float(mtparams['nodal-plane-1-strike']),
                                'dip':float(mtparams['nodal-plane-1-dip']),
                                'rake':float(mtparams['nodal-plane-1-rake'])}
        tensor_params['NP2'] = {'strike':float(mtparams['nodal-plane-2-strike']),
                                'dip':float(mtparams['nodal-plane-2-dip']),
                                'rake':float(mtparams['nodal-plane-2-rake'])}
        return tensor_params


    def getEventProperties(self,eventid):
        try:
            eurl = EVENT_URL.replace('EVENTID',eventid)
            fh = urlopen(eurl)
            data = fh.read().decode('utf-8')
            fh.close()
            jdict = json.loads(data)
            lon,lat,depth = jdict['geometry']['coordinates']
            tensor_params = self.getPreferredMomentTensor(eventid,jdict=jdict)
            return lat,lon,depth,tensor_params
        except Exception as e:
            raise(e)
