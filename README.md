<h2>NOAA Aeris N2O/CO Instrument Software</h2>

<p>The main program to run the Aeris instrument equipped with a multi-position Valco valve is aeris.py. Run aeris.py -h to see the various options for the program.</p>

<p>Run aeris.py without options to use the valve sequence programed in the config.py file. The aeris.py program will store the output of the Aeris
instrument to a .csv file. To read the csv file into a pandas data frame.</p>
<pre><code>df = pd.read_csv(file, infer_datetime_format=True, parse_dates=True, index_col='datetime')</code></pre>
