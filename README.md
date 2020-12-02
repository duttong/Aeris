<h2>Aeris N2O/CO Instrment software</h2>

<p>Run aeris.py without options to use the valve sequence programed in
the config.py file. The aeris.py program will store the output of the Aeris
instrument to a .csv file.</p>

<p>To read the csv file into a pandas data frame.</p>
<p>df = pd.read_csv(file, infer_datetime_format=True, parse_dates=True, index_col='datetime')</p>
