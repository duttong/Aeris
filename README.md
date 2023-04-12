<h2>NOAA Aeris N2O/CO Instrument Software</h2>

<p>The main program to run the Aeris instrument equipped with a multi-position Valco valve is <strong>aeris.py</strong>. Run <strong>aeris.py -h</strong> to see the various options for the program.</p>

<h3>Initial Setup</h3>
<p>1. The Aeris instrument should be configured to send data out the USB port (see manual)</p>
<p>2. Edit the <strong>config.py</strong> file with the Valco valve and Aeris serial port settings.</p>
<p>3. Change the valve sequence and duration in <strong>config.py</strong>.</p>

<p>Run <strong>aeris.py</strong> without options to use the valve sequence programed in the config.py file. The <strong>aeris.py</strong> program will store the output of the Aeris instrument to a .csv file.</p>

<h3>To read the Aeris .csv data file into a python pandas dataframe.</h3>
<pre><code>df = pd.read_csv(file, infer_datetime_format=True, parse_dates=True, index_col='datetime')</code></pre>
<p>call <strong>stats.py</strong> aeris_datafile.csv for basic stats</p>

<h3>Disclaimer</h3>
<p>This repository is a scientific product and is not official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project code is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.</p>
