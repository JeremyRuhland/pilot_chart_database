#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converts global surface level wind data from ARL gdas weekfiles into a
sqlite3 DB. This is used as part of the pilot chart database project and is
executed by the pilot chart database generator shell script.
Estimated execution time for 10 years of data is 4h.

Schema is (timestamp, lat, lon, windDir, windVel) stored as real (float64).

Timestamp is the unix epoch time of the data product (every 3h).
windDir and windVel are a polar coordinate vector for each 1-degree grid
square.
"""

__title__ = 'GDAS Wind Data Ingestor'
__author__ = 'Jeremy Ruhland'
__email__ = 'jeremy (at) goopypanther.org'
__license__ = 'GPL3'
__copyright__ = 'Copyright 2020 Jeremy Ruhland'
__version__ = '0.1'

import pyximport
import ARLreader.ARLreader as Ar
import os
import datetime
import numpy as np
import sqlite3
import logging


def getArlDays(weekFile):
    """
    Calculate number of days of records in ARL week file
    Most week files have 7 days of data but w5 files have 1-3 and who knows
    how dependable that all is.

    :param weekFile: Ar.reader object, read file must be in active directory
    :return: int Number of days contained in week file
    """

    fileSizeBytes = os.path.getsize(weekFile.fname)
    recordLen = 65210
    numRecordsInWeekFile = fileSizeBytes/recordLen

    gridRecord = 1
    numRecordsInLevels = sum([len(weekFile.levels[level]['vars']) for level in weekFile.levels])
    recordsPerTimestep = gridRecord + numRecordsInLevels
    timesteps = 8
    numRecordsPerDay =  recordsPerTimestep * timesteps

    numDays = int(numRecordsInWeekFile/numRecordsPerDay)

    return (numDays)


# Hack to enable fast_funcs to accelerate Ar.unpack_data()
# Importing ARLreader from current directory without installing breaks its
# relative pyximport of fast_funcs. I assume the right way to do this is venv.
# We just call pyximport and import fast_funcs manually, add it to Ar and flip
# the enable bool.
pyximport.install()
import ARLreader.ARLreader.fast_funcs as  fast_funcs
Ar.fast_funcs = fast_funcs
Ar.fastfuncsavail = True
print('fast_funcs now available')

# Surface level winds @ 20hPa
windHeightLevel = 20

# Turn off logging messages
Ar.logger.setLevel(logging.WARNING)

# Connect to/create sqlite database
db = sqlite3.connect('gdas_global_wind_decade.sqlite3')
dbc = db.cursor()

# Set up tables
dbc.execute("CREATE TABLE wind (month integer, lat integer, lon integer, windDir real, windVel real)")

# Collect all gdas weekfiles in directory
gdasFiles = [x for x in os.listdir() if ('gdas1' and '.w') in x]

dataTable = []

# Loop for all files
for weekFileNum, weekFile in enumerate(gdasFiles):
    print('F{}/{}'.format(weekFileNum + 1, len(gdasFiles)))

    ArlData = Ar.reader(weekFile)

    daysInWeekFile = getArlDays(ArlData)

    # Loop for each day
    for dayNum in range(ArlData.indexinfo.d, ArlData.indexinfo.d + daysInWeekFile):
        print(' D{}/{}'.format(dayNum, ArlData.indexinfo.d + daysInWeekFile - 1))

        # Loop for each 3h data grid
        for hourNum in (range(0, 24, 3)):
            print('  H{}'.format(hourNum))

            # Extract velocity data for wind field
            record, grid, dataV = ArlData.load_heightlevel(dayNum, hourNum, windHeightLevel, 'VWND')
            record, grid, dataU = ArlData.load_heightlevel(dayNum, hourNum, windHeightLevel, 'UWND')

            # Convert wind field velocity data to polar vector
            windDir, windVel = Ar.wind_from_components(dataU, dataV)

            # Create timestamp for this wind field
            #windTime = datetime.datetime((2000 + ArlData.indexinfo.y), ArlData.indexinfo.m, dayNum, hourNum).timestamp()
            windMonth = ArlData.indexinfo.m

            # Assemble lists of [timestamp, lat, lon, windDir, windVel] for dataTable
            # x is a tuple of type ((lon, lat), val)
            for x in np.ndenumerate(windDir):
                # Idx values are used to access lat & lon co-ordinates from grid tuple
                lonIdx = x[0][0]
                latIdx = x[0][1]

                lat = grid[0][latIdx]
                lon = grid[1][lonIdx]
                windDirVal = x[1]
                windVelVal = windVel[lonIdx][latIdx]

                dataTable.append((windMonth, lat, lon, windDirVal, windVelVal))

        # Write daily wind data to database
        # Weekly wind data writes are more efficent but there is some internal
        # limit that truncates beyond ~6 days of data.
        if len(dataTable) >= 3127680:
            dbc.executemany("INSERT INTO wind VALUES (?, ?, ?, ?, ?)", dataTable)
            dataTable = []

if len(dataTable) >= 1:
    dbc.executemany("INSERT INTO wind VALUES (?, ?, ?, ?, ?)", dataTable)

# Close database
db.commit()
db.close()
