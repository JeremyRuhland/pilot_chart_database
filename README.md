# Pilot Chart Database Generator

Pilot charts are a navigation tool which displays prevailing wind, current and wave information on a per-month basis for the world's oceans. These charts are traditionally printed on paper and although digital formats are available for computerized chartplotters (openCPN, etc.) these files are essentially raster images of their paper counterparts.

This project is an attempt to create a machine readable database of pilot chart information to feed into custom sailboat path planning software.

The script starts by downloading the previous decade of global weather data files from the [NOAA ARL](https://www.arl.noaa.gov/) server and then processes them using python to produce a sqlite database of wind direction and speed. This database is then processed by a second program which calculates numerical representations of windroses which are written to a pilot chart database.

The wind direction/speed database product is also useful for mission simulation.

### Installation
Install pyximport and numpy. Pyximport was unable to find numpy headers when I installed via pip3 despite the files being in the right place but apt-get install works fine.

After cloning repo, initialize submodules to pull down [ARLreader](https://github.com/martin-rdz/ARLreader)

```bash
sudo apt-get install python3-pyximport python3-numpy

git submodule init
git submodule update
```

### Running
Run `./pilot_chart_database_generator.sh` to begin the process.

Data download takes about a day on a broadband connection and requires around 321Gb of storage space.

The `gdas_global_wind_decade.sqlite3` database will be approximately 12Gb and can be compressed with bz2 to 6Gb. Database creation takes about 8 hours.

The final pilot chart database will be approximately xxMb. Processing takes about xxmin.

### Future
Preliminary profiling shows majority of time in database generator is spent executing writes to the DB. Batching multiple weeks worth of writes will speed this up with memory use tradeoff (how much?). Parallelization could also provide smaller magnitude speedup but requires same memory increase.

Additional data which would be useful to include in the pilot chart database at some future point is:

 * Ocean currents
 * Wave height
 * Cloud cover
