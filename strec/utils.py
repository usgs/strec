from math import cos,sin,pi
import os.path
import configparser
import shutil

STRECINI = 'strec.ini'
GCMT_OUTPUT = 'gcmt.db'

def deleteConfig():
    homedir = os.path.expanduser('~') #where is the user's home directory
    if homedir == '~':
        return
    configfolder = os.path.join(homedir,'.strec')
    try:
        shutil.rmtree(configfolder)
    except:
        return
    return

def getConfig():
    homedir = os.path.expanduser('~') #where is the user's home directory
    if homedir == '~':
        msg = 'Could not establish home directory for %s.  Exiting.' % getpass.getuser()
        raise Exception(msg)
    configfolder = os.path.join(homedir,'.strec')
    if not os.path.isdir(configfolder):
        os.mkdir(configfolder)
    configfile = os.path.join(configfolder,STRECINI)
    if not os.path.isfile(configfile):
        #here we should create one from the default
        thispath = os.path.dirname(os.path.abspath(__file__)) #where is this file?
        tmpfile = os.path.join(thispath,'data','strec.ini')
        config = configparser.ConfigParser()
        config.readfp(open(tmpfile))
        return config,configfile
    config = configparser.ConfigParser()
    config.readfp(open(configfile))
    return (config,configfile)

def isNaN(x):
    return str(x) == str(1e400*0)

def splitWithCommas(line):
    if line.find('"') == -1:
        return line.split(',')
    nquotes = line.count('"')
    idx1 = 0
    linelist = list(line)
    for i in range(0,nquotes/2):
        idx1 = linelist.index('"',idx1)
        idx2 = linelist.index('"',idx1+1)
        lineseg = linelist[idx1:idx2+1]
        if lineseg.count(','):
            lineseg = list(''.join(lineseg).replace(',','|'))
            linelist[idx1:idx2+1] = lineseg
        idx1 = idx2+1
    line = ''.join(linelist)
    parts = line.split(',')
    newparts = []
    for p in parts:
        p = p.replace('"','')
        newparts.append(p.replace('|',','))
    return newparts

def cosd(input):
    """
    Returns cosine of angle given in degrees.
    """
    return cos(input * pi/180)

def sind(input):
    """
    Returns sine of angle given in degrees.
    """
    return sin(input * pi/180)
