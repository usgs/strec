import io
from urllib import request, parse
import gzip
import tempfile
import os.path
from datetime import datetime


# third party libraries
import numpy as np
import pandas as pd


TIMEOUT = 30
HIST_GCMT_URL = (
    "http://www.ldeo.columbia.edu/~gcmt/projects/CMT/catalog/jan76_dec17.ndk.gz"
)
MONTHLY_GCMT_URL = (
    "http://www.ldeo.columbia.edu/~gcmt/projects/CMT/catalog/NEW_MONTHLY/"
)


def fetch_gcmt():
    """Fetch all GCMT data from gcmt web site, return into pandas DataFrame.

    Returns:
        pandas DataFrame containing columns:
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
    t1 = str(datetime.utcnow())
    print("%s - Fetching historical GCMT data..." % t1)
    histfile = get_historical_gcmt()
    t2 = str(datetime.utcnow())
    print("%s - Converting to dataframe..." % t2)
    dataframe = ndk_to_dataframe(histfile)
    t3 = str(datetime.utcnow())
    print("%s - Fetching monthly data..." % t3)
    start_year = 2018
    end_year = datetime.utcnow().year
    end_month = datetime.utcnow().month
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if year == end_year and month > end_month:
                continue
            print("Fetching GCMT data for %i month %i..." % (year, month))
            monthfile = get_monthly_gcmt(year, month)
            if monthfile is None:
                print("No NDK file for %i month %i" % (year, month))
                continue
            month_frame = ndk_to_dataframe(monthfile)
            dataframe = dataframe.append(month_frame)
    return dataframe


def get_historical_gcmt():
    """Retrieve the Jan 1976 - Dec 2010 GCMT catalog.

    NDK format explained:

    http://www.ldeo.columbia.edu/~gcmt/projects/CMT/catalog/allorder.ndk_explained

    Returns:
        io.StringIO:
            StringIO object containing the NDK file for the 1976-2010 period.
    """
    zipfile = None
    try:
        fh = request.urlopen(HIST_GCMT_URL)
        zip_bytes = fh.read()
        fh.close()
        handle, zipfile = tempfile.mkstemp()
        os.close(handle)
        f = open(zipfile, "wb")
        f.write(zip_bytes)
        f.close()
        gz = gzip.GzipFile(zipfile, mode="rb")
        unzip_bytes = gz.read().decode("utf-8")
        string_unzip = io.StringIO(unzip_bytes)
        return string_unzip
    except Exception as msg:
        raise Exception(msg)
    finally:
        if zipfile is not None:
            os.remove(zipfile)


def get_monthly_gcmt(year, month):
    """Download one month's worth of GCMT data into a StringIO object.

    Args:
        year (int):
            Integer year.
        month (int):
            Integer month (1-12).
    Returns:
        io.StringIO:
            StringIO object containing NDK file for given month/year.
    """
    strmonth = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ][month - 1]
    stryear = str(year)
    url = parse.urljoin(
        MONTHLY_GCMT_URL, os.path.join(stryear, strmonth + stryear[2:] + ".ndk")
    )
    try:
        fh = request.urlopen(url, timeout=TIMEOUT)
        bytes = fh.read().decode("utf-8")
        fh.close()
        stringfile = io.StringIO(bytes)
        return stringfile
    except Exception:
        return None


def ndk_to_dataframe(ndkfile):
    """Turn an ndk file-like object or filename into a pandas dataframe.

    Args:
        ndkfile (str or file-like object):
            String file name or file-like object containing NDK-formatted earthquake
            data.
    Returns:
        pandas DataFrame containing columns:
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
    if not hasattr(ndkfile, "read"):
        ndkfile = open(ndkfile, "r")

    lc = 0
    df = pd.DataFrame(
        columns=[
            "time",
            "lat",
            "lon",
            "depth",
            "mag",
            "mrr",
            "mtt",
            "mpp",
            "mrt",
            "mrp",
            "mtp",
        ]
    )
    tdict = {}
    for line in ndkfile.readlines():
        if (lc + 1) % 5 == 1:
            _parse_line1(line, tdict)
            lc += 1
            continue
        if (lc + 1) % 5 == 2:
            lc += 1
            continue
        if (lc + 1) % 5 == 3:
            lc += 1
            continue
        if (lc + 1) % 5 == 4:
            _parse_line4(line, tdict)
            lc += 1
            continue
        if (lc + 1) % 5 == 0:
            _parse_line5(line, tdict)
            lc += 1
            tdict.pop("exponent")  # remove now extraneous field
            df = df.append(tdict, ignore_index=True)
            tdict = {}
            continue

    ndkfile.close()
    return df


def _parse_line1(line, tdict):
    """Parse the first line of an NDK file.

    Args:
        line (str/byte):
            The line of the NDK file
        tdict (dict):
            dictionary to inpiut values from ndk files

    """
    dstr = line[5:26]
    year = int(dstr[0:4])
    month = int(dstr[5:7])
    day = int(dstr[8:10])
    hour = int(dstr[11:13])
    minute = int(dstr[14:16])
    fseconds = float(dstr[17:])
    seconds = int(fseconds)
    if seconds > 59:
        seconds = 59
    microseconds = int((fseconds - seconds) * 1e6)
    if microseconds > 999999:
        microseconds = 999999

    tdict["time"] = datetime(year, month, day, hour, minute, seconds, microseconds)

    tdict["lat"] = float(line[27:33])
    tdict["lon"] = float(line[34:41])
    tdict["depth"] = float(line[42:47])


def _parse_line4(line, tdict):
    """Parse the fourth line of an NDK file.

    Args:
        line (str/byte):
            The line of the NDK file
        tdict (dict):
            dictionary to inpiut values from ndk files
    """
    tdict["exponent"] = float(line[0:2])
    tdict["mrr"] = float(line[2:9]) * np.power(10.0, tdict["exponent"])
    tdict["mtt"] = float(line[15:22]) * np.power(10.0, tdict["exponent"])
    tdict["mpp"] = float(line[28:35]) * np.power(10.0, tdict["exponent"])
    tdict["mrt"] = float(line[41:48]) * np.power(10.0, tdict["exponent"])
    tdict["mrp"] = float(line[54:61]) * np.power(10.0, tdict["exponent"])
    tdict["mtp"] = float(line[67:74]) * np.power(10.0, tdict["exponent"])


def _parse_line5(line, tdict):
    """Parse the fifth line of an NDK file.

    Args:
        line (str/byte):
            The line of the NDK file
        tdict (dict):
            dictionary to inpiut values from ndk files
    """
    scalar_moment = float(line[49:56].strip()) * np.power(10.0, tdict["exponent"])
    tdict["mag"] = ((2.0 / 3.0) * np.log10(scalar_moment)) - 10.7
