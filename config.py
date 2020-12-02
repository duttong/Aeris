from datetime import datetime

ssv_add = 1
ssv_port = '/dev/cu.usbserial-14640'
aeris_port = '/dev/cu.usbserial-1420'

aeris_logfile = 'aeris-log.txt'
aeris_datafile = f'aeris-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}.csv'

# create a basic valve sequence
repeat = 2      # number of times to repeat valve sequence
dur = 60        # seconds on each port
valve_seq = [1, 2, 3, 4]

seq = [(pos, n, dur) for n in range(repeat) for pos in valve_seq]
