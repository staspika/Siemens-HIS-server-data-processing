#!/usr/bin/env python3
# -*- encoding: utf-8-*-

from __future__ import print_function, unicode_literals, division
from pylab import *
import pandas
import itertools
import seaborn
import easygui
import configparser
import sys

print(sys.version)
config = configparser.ConfigParser()
config.read("config.ini")
dir_src_data = config['Paths']['DirSourceData'].strip('"')
dir_images = config['Paths']['DirImages'].strip('"')
seaborn.set(color_codes=True)
seaborn.set_style('whitegrid')
seaborn.set_style('ticks')

# Read Siemens HIS file
filenames = easygui.fileopenbox(default=dir_src_data+"/*.csv", multiple=True)
for filename in filenames:
    sitename = filename.split('.')[0]
    X = pandas.read_csv(filename, skipinitialspace=True, comment="#")
    # Convert time stamp to a nicer format
    X['Time stamp'] = pandas.to_datetime(X['Time stamp'], infer_datetime_format=True)
    X['Milliseconds'] = pandas.to_timedelta(X['Milliseconds'], unit='ms')
    X['Time stamp'] = X['Time stamp'] + X['Milliseconds']
    X = X.drop('Milliseconds', axis=1)
    X = X.sort_values('Time stamp')
    for pointname in set(X['Point Name']):
        mask = (X['Point Name'] == pointname)
        timeline = X[mask]['Time stamp']
        stat = X[mask]['Status']
        # Plot state
        with seaborn.axes_style('whitegrid'):
            figure()
            plot(timeline, stat, drawstyle='steps-post')
            seaborn.despine()
            xlabel('Time')
            ylabel('Status')
            yticks([1, 0, -1, -2], ['In', 'Out', 'Fault', 'Intermediate'])
            axis('tight')
            title(pointname)
            savefig("{0}/{1}".format(dir_images, pointname.replace('/', '-')+'-01-status.png'))
            close()
        # Plot statistics
        with seaborn.axes_style('whitegrid'):
            figure()
            mask = [n==0 or n==1 for n in stat]
            stat = stat[mask]
            timeline=timeline[mask]
            dt = diff(timeline)
            ds = diff(stat)
            mask = [n>0 for n in ds]
            disconnections = [n for n in list(itertools.compress(dt, mask))]
            disc_sec = disconnections / timedelta64(1, 's')
            distr = logspace(-1, 7, 9, endpoint=True)
            seaborn.distplot(disc_sec, bins=distr, hist=True, kde=False, rug=True)
            seaborn.despine()
            xscale('log')
            xlabel('Duration of disconnection, s')
            ylabel('Number of disconnections (total {0})'.format(len(disconnections)))
            title(pointname)
            savefig("{0}/{1}".format(dir_images, pointname.replace('/', '-')+'-02-histogram.png'))
            close()
