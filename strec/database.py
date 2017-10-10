#stdlib imports
import sqlite3
import os.path
from datetime import datetime
from collections import OrderedDict

#third party imports
import pandas as pd
import numpy as np

SCHEMA = OrderedDict([('time','datetime'),
                      ('sourceid','integer'),
                      ('lat','float'),
                      ('lon','float'),
                      ('depth','float'),
                      ('mag','float'),
                      ('mrr','float'),
                      ('mtt','float'),
                      ('mpp','float'),
                      ('mrt','float'),
                      ('mrp','float'),
                      ('mtp','float')])

TIMEFMT = '%Y-%m-%d %H:%M:%S.%f'

def stash_dataframe(dataframe,datafile,source,create_db=False):
    """Store a dataframe in the database.

    :param Dataframe:
      pandas Dataframe, containing columns:
        - time (YYYY-MM-DD HH:MM:SS for CSV)
        - lat (decimal degrees)
        - lon (decimal degrees)
        - depth (km)
        - mag Magnitude
        - mrr Mrr moment tensor component
        - mtt Mtt moment tensor component
        - mpp Mpp moment tensor component
        - mrt Mrt moment tensor component
        - mrp Mrp moment tensor component
        - mtp Mtp moment tensor component
    """
    if create_db:
        if os.path.isfile(datafile):
            os.remove(datafile)
        conn = sqlite3.connect(datafile)
        cursor = conn.cursor()
        nuggets = []
        for key,value in SCHEMA.items():
            nuggets.append('%s %s' % (key,value))
        create_stmt = 'CREATE TABLE earthquake (%s)' % (','.join(nuggets))
        cursor.execute(create_stmt)
        source_stmt = 'CREATE TABLE source (id integer primary key, source text)'
        cursor.execute(source_stmt)
    else:
        conn = sqlite3.connect(datafile)
        cursor = conn.cursor()

    cursor.execute('SELECT id from source where source = "%s"' % source.lower())
    sourcerow = cursor.fetchone()
    if sourcerow is not None:
        sourceid = sourcerow[0]
        dataframe['sourceid'] = sourceid
    else:
        cursor.execute('INSERT INTO source (source) values ("%s")' % source.lower())
        conn.commit()
        cursor.execute('SELECT id from source where source = "%s"' % source.lower())
        sourceid = cursor.fetchone()[0]
        dataframe['sourceid'] = sourceid

    dataframe.to_sql('earthquake',conn,if_exists='append',index=False)
        
    conn.close()
    
def fetch_dataframe(datafile):
    """Return a pandas dataframe containing earthquake information.

    :param datafile:
      Path to sqlite3 database file.
    :returns:
      pandas Dataframe, containing columns:
        - time (YYYY-MM-DD HH:MM:SS for CSV)
        - lat (decimal degrees)
        - lon (decimal degrees)
        - depth (km)
        - mag Magnitude
        - mrr Mrr moment tensor component
        - mtt Mtt moment tensor component
        - mpp Mpp moment tensor component
        - mrt Mrt moment tensor component
        - mrp Mrp moment tensor component
        - mtp Mtp moment tensor component
    """
    conn = sqlite3.connect(datafile)
    cursor = conn.cursor()
    dataframe = pd.read_sql('SELECT * FROM earthquake',conn)

    #get the data source information
    dataframe['source'] = ''
    usources = dataframe['sourceid'].unique()
    for source in usources:
        cursor.execute('SELECT source FROM source WHERE id=%i' % source)
        tsource = cursor.fetchone()[0]
        rowidx = dataframe['sourceid'] == source
        dataframe.loc[rowidx,'source'] = tsource

    dataframe.drop('sourceid',axis=1,inplace=True)
        
    conn.close()
    return dataframe
