import os.path
import configparser

STRECINI = 'strec.ini'
GCMT_OUTPUT = 'gcmt.db'

CONSTANTS = {'minradial_disthist' : 0.01,
             'maxradial_disthist' : 1.0,
             'minradial_distcomp' : 0.5,
             'maxradial_distcomp' : 1.0,
             'step_distcomp' : 0.1,
             'depth_rangecomp' : 10,
             'minno_comp' : 3,
             'default_szdip' : 17,
             'dstrike_interf' : 30,
             'ddip_interf' : 30,
             'dlambda' : 60,
             'ddepth_interf' : 20,
             'ddepth_intra' : 10}

def get_config(datafolder=None):
    homedir = os.path.expanduser('~') #where is the user's home directory
    if homedir == '~':
        msg = 'Could not establish home directory for %s.  Exiting.' % getpass.getuser()
        raise(Exception(msg))
    configfolder = os.path.join(homedir,'.strec')
    if not os.path.isdir(configfolder):
        os.mkdir(configfolder)
    configfile = os.path.join(configfolder,STRECINI)
    if not os.path.isfile(configfile):
        if datafolder is None:
            return (None,None)
        #here we should create one from the default data above and input datafolder
        config = configparser.ConfigParser()
        config['CONSTANTS'] = CONSTANTS
        config['DATA'] = {'folder':datafolder,
                          'dbfile':'moment_tensors.db'}

        with open(configfile, 'w') as f:
            config.write(f)
        return (config,configfile)
    
    config = configparser.ConfigParser()
    config.readfp(open(configfile))
    return (config,configfile)

