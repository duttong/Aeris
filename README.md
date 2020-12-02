<h2>NOAA Aeris N2O/CO Instrument Software</h2>

<p>Run aeris.py without options to use the valve sequence programed in
the config.py file. The aeris.py program will store the output of the Aeris
instrument to a .csv file.</p>

<h4>To read the csv file into a pandas data frame.</h4>
<p>df = pd.read_csv(file, infer_datetime_format=True, parse_dates=True, index_col='datetime')</p>
