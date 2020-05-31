#! /bin/sh

# @file 
# @brief ARL Weather data download
#
# @author Jeremy Ruhland <jeremy ( a t ) goopypanther.org>
#
# @copyright Jeremy Ruhland 2020
# @version 1.0
# @since May 25, 2020


HOST='ftp://arlftp.arlhq.noaa.gov'
DIR='pub/archives/gdas1'

# Download list of available files
wget $HOST/$DIR/listing

# Filter list to previous decade of data
DOWNLOAD_LIST=$(egrep "09|10|11|12|13|14|15|16|17|18|19" listing)


# Download previous decade of data using parallel threads.
# WARNING: This will download ~321Gb of data and use a lot of bandwidth.
# Server seems to limit each connection to 1.3mbps, I was able to pull nearly
# 24mbps total without issue and download the archive in just over a day.
# Adjust xargs -P20 flag as needed.

# Split xargs on whitespace, run max 20 threads with one item each
echo $DOWNLOAD_LIST | xargs -I{} -d " " -n1 -P20 wget "$HOST/$DIR/{}"


# Ingest ARL data and filter out surface level winds. Export database to file.
python3 ./gdas_wind_data_ingestor.py

# Process wind database and export pilot chart database
# TODO
