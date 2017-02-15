# WebKeezer

Control freezer temperature to keep kegs cold.

## Install

This project is meant to run on an Onion Omega2 (https://onion.io/). The python
script is written for Python 2.7.

To install:
1. Copy the files to the Omega2. If not in /root, you'll need to change some paths.

2. Follow the 1-wire setup instructions at:
https://wiki.onion.io/Tutorials/Reading-1Wire-Sensor-Data

3. A crontab file should be started:
* * * * * /usr/bin/python /root/tempcontrol.py

## Code

The script tempcontrol.py switches a relay on/off based on a temperature and 
the setpoint and temperature delta defined in lines 1 and 2 of keezerparams.txt.


## Run

Start the cron job with:

/etc/init.d/cron enable
/etc/init.d/cron start
