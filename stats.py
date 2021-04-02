#! /usr/bin/env python

import pandas as pd
import numpy as np
import argparse


def pct(x):
    return np.std(x)/np.mean(x)*100


opt = argparse.ArgumentParser(description='Quick stats on Aeris data file.')
opt.add_argument('csvfile', help='Aeris .csv data file.')
options = opt.parse_args()

file = options.csvfile
df = pd.read_csv(file, infer_datetime_format=True, parse_dates=True, index_col='datetime')
df = df.sort_index()

# state keeps track of ssv transitions
df['state'] = (df['ssv'].diff() != 0).cumsum()

# discard the first 1/3 of the data after a ssv switch
df2 = df.groupby(['state'], as_index=False).apply(lambda x: x.iloc[x.ssv.size//3:]).reset_index(level=0, drop=True)

# stats on each ssv position for each valve sequence
print(df2.groupby(['state', 'seq_count', 'ssv'])[['n2o', 'co']].agg(['mean', 'std', pct, 'count']))

# stats on each ssv position for all valve sequences.
print('\n\nStatistics on each SSV:\n')
print(df2.groupby(['ssv'])[['n2o', 'co']].agg(['mean', 'std', pct, 'count']))
