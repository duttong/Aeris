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
df2 = df.groupby(['seq_count', 'ssv'], as_index=False).apply(lambda x: x.iloc[x.ssv.size//3:]).reset_index(level=0, drop=True)
print(df2.groupby(['seq_count', 'ssv'])['n2o', 'co'].agg(['mean', 'std', pct, 'count']))
