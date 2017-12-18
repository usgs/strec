#!/usr/bin/env python

import pandas as pd
from datetime import datetime
import tempfile
import sqlite3
import os.path

from strec.database import stash_dataframe, fetch_dataframe


def test_stash():
    d = {'time': [pd.Timestamp(datetime.utcnow()), pd.Timestamp(datetime.utcnow())],
         'lat': [34.123, 17.123],
         'lon': [-118.123, 120.123],
         'depth': [51.4, 12.7],
         'mag': [7.5, 6.4],
         'mrr': [1.2e26, 1.4],
         'mpp': [2.3e26, 1.3],
         'mtt': [3.4e26, 2.5],
         'mrt': [4.5e26, 6.5],
         'mrp': [5.6e26, 4.3],
         'mtp': [6.7e26, 2.7]}
    df = pd.DataFrame(d)

    d1 = {'time': [pd.Timestamp(datetime.utcnow()), pd.Timestamp(datetime.utcnow())],
          'lat': [34.125, 17.123],
          'lon': [-118.323, 120.123],
          'depth': [51.2, 12.7],
          'mag': [7.5, 6.4],
          'mrr': [1.2e26, 1.4],
          'mpp': [2.3e26, 1.3],
          'mtt': [3.4e26, 2.5],
          'mrt': [4.5e26, 6.5],
          'mrp': [5.6e26, 4.3],
          'mtp': [6.7e26, 2.7]}
    df1 = pd.DataFrame(d1)

    d2 = {'time': [pd.Timestamp(datetime.utcnow()), pd.Timestamp(datetime.utcnow())],
          'lat': [34.127, 17.128],
          'lon': [-118.323, 120.123],
          'depth': [51.2, 12.7],
          'mag': [7.5, 6.4],
          'mrr': [1.2e26, 1.4],
          'mpp': [2.3e26, 1.3],
          'mtt': [3.4e26, 2.5],
          'mrt': [4.5e26, 6.5],
          'mrp': [5.6e26, 4.3],
          'mtp': [6.7e26, 2.7]}
    df2 = pd.DataFrame(d2)

    dfile = None
    try:
        f, dfile = tempfile.mkstemp()
        os.close(f)
        stash_dataframe(df, dfile, 'gcmt', create_db=True)

        stash_dataframe(df1, dfile, 'usmww', create_db=False)

        stash_dataframe(df2, dfile, 'usmww', create_db=False)

        conn = sqlite3.connect(dfile)

        cursor = conn.cursor()

        cursor.execute('SELECT mrr FROM earthquake')
        rows = cursor.fetchall()
        assert rows[0][0] == 1.2e26

        df2 = fetch_dataframe(dfile)
        assert df2['mtt'][0] == df['mtt'][0]
        cursor.close()
        conn.close()
    except AssertionError as ae:
        raise AssertionError(str(ae))
    except Exception as e:
        pass
    finally:
        if dfile is not None:
            os.remove(dfile)


if __name__ == '__main__':
    test_stash()
