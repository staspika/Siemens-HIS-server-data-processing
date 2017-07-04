#!/usr/bin/env python3

from pylab import *
from datetime import datetime, timedelta
from pathlib import PurePath
import dateutil
import csv
import json
import glob
import itertools
import re
import os
import seaborn
import json

seaborn.set_style("white")
seaborn.set_style("ticks")

with open('config.json') as config_file:
    gconf = json.load(config_file)

path_root = PurePath(gconf['dir.root'])
path_srcdata = PurePath(gconf['dir.data'])
path_images = PurePath(gconf['dir.images'])
csv.register_dialect('his', delimiter = ',', skipinitialspace = True)
his_timestamp_format = '%m/%d/%Y %H:%M:%S'

def readTimestamp(timestamp):
    k = timestamp.find('*')
    if k >= 0:
        if timestamp[k-1] == ' ':
            timeshift = -1
        elif timestamp[k+1] == ':':
            timeshift = +1
        timestamp = ''.join(timestamp.split('*'))
    ts = datetime.strptime(timestamp, his_timestamp_format)
    return ts

def readRawData(filename):
    w = []
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile, dialect='his')
        for row in reader:
            timestamp = readTimestamp(row['Time stamp']) + timedelta(seconds=0.001*int(row['Milliseconds']))
            w.append({'Path': row['Point Name'],
                      'Timestamp': timestamp,
                      'Value': float(row['Value']),
                      'Status': int(row['Status']),
                      'Source / Quality': row['Source / Quality'],
                      'Measurement units': row['Measurement Units']})
    return w

def diff(n):
    m = []
    for i in range(1, len(n)):
        k = n[i]-n[i-1]
        m.append(k)
    return m

data_files = glob.iglob(path_srcdata.joinpath("*.csv").as_posix())
t_start = dateutil.parser.parse('2016-01-01T00:00')
t_stop = dateutil.parser.parse('2017-01-01T00:00')
print('For the selected period ({0} – {1}):'.format(t_start, t_stop))
for src_file in data_files:
    name = os.path.basename(src_file)
    w = readRawData(src_file)
    with open("./data/{0}.json".format(name), "w") as json_file:
        json.dump(w, json_file, default=str)
    timeline = [x['Timestamp'] for x in w]
    stat = [x['Status'] for x in w]
    mask = [(t>=t_start) and (t<=t_stop) for t in timeline]
    print('{0}: {1} records'.format(name, mask.count(True)))
    if mask.count(True) > 1: # If there are data for the selected period, make graphs
        timeline = list(itertools.compress(timeline, mask))
        stat = list(itertools.compress(stat, mask))
        fig0 = figure()
        plot(timeline, stat, drawstyle='steps-post')
        ylim([-2.2, 1.2])
        xlabel('Time')
        ylabel('Status')
        yticks([-2, -1, 0, 1])
        title(name)
        fig0.savefig(path_images.joinpath(name + '.state.png').as_posix())
        mask = [n==0 or n==1 for n in stat]
        timeline = list(itertools.compress(timeline, mask))
        stat = list(itertools.compress(stat, mask))
        close('all')
        # Calculate disconnections
        # A disconnection period is a time difference between first zero after a one and a first one after a zero
        mask = full(len(stat), True)
        for i in range(1, len(stat)):
            if stat[i] == stat[i-1]:
                mask[i] == False
        if mask.all() != True:
            print("Duplicate values in state array!")
            timeline = list(itertools.compress(timeline, mask))
            stat = list(itertools.compress(stat, mask))
        dt = diff(timeline)
        ds = diff(stat)
        mask = [n>0 for n in ds]
        disconnections = [n for n in list(itertools.compress(dt, mask))]
        disc_sec = [n.total_seconds() for n in disconnections]
        gDisc = disconnections
        gStat = stat
        gTime = timeline
        fig1 = figure()
        #~ seaborn.distplot(disc_sec, rug=True, kde=False)
        hist(disc_sec, bins=logspace(-1, 7, 9, endpoint=True))
        #~ vlines(disc_sec, 0, 5)
        xscale('log')
        xlabel('Duration of disconnection, s')
        ylabel('Number of disconnections')
        title(src_file)
        savefig(path_images.joinpath(name + '.hist.png').as_posix())
        close('all')
