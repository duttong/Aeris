#! /usr/bin/env python

import serial
from time import sleep
import argparse
import logging

from valco import SSV
import config as cfg


class Aeris:

    partial = ''

    def __init__(self):
        self.start_logger()
        self.aeris = self.aeris_connect()

    def start_logger(self):
        file = f'{cfg.aeris_logfile}'
        logging.basicConfig(filename=file, filemode='w',
                level=logging.DEBUG,
                format='%(asctime)s.%(msecs)03d, %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d, %H:%M:%S')

    def aeris_connect(self):
        """ Setup serial connection to Aeris N2O/CO instrument """
        print(f'Connecting to Aeris on port {cfg.aeris_port}')
        ser = serial.Serial(cfg.aeris_port, timeout=0.05, baudrate=9600)
        ser.flushInput()
        return ser

    def read_data(self):
        """ Reads all data in the serial port buffer. """
        try:
            data = self.aeris.read_all().decode()
        except UnicodeDecodeError:
            data = ''

        return data

    def valid_packet(self, packet):
        """ Criteria for a full data packet from the Aeris instrument.
            A valid packet has 9 cells of data and the first cell is
            exactly 23 characters (MM/DD/YYYY HH:MM:SS.sss) """
        datums = list(filter(None, packet.split(',')))
        if len(datums) != 9 or len(datums[0]) != 23:
            return False
        return True

    def return_packets(self):
        """ Parses data from the Aeris instrument. If the serial
            port is read while data is coming from the instrument, the packet
            will be cut into a partial packet. The parsing routine saves
            the partial packet and appends the remainder after the next
            serial port read. """
        data = self.read_data()
        packets = []

        if len(data) == 0:
            return packets

        # handle a scenario where the \r\n charaters are split across
        # two packets.
        if data[-1] == '\r':
            data += '\n'
        if data[0] == '\n':
            data = data[1:]

        # parse data packets between \r\n
        for packet in filter(None, data.split('\r\n')):
            if not self.valid_packet(packet):
                # not a complete packet, add next packet to it.
                self.partial = self.partial + packet
                if self.valid_packet(self.partial):
                    packets.append(self.partial)
                    self.partial = ''
                elif len(self.partial) > 90:
                    # something went wrong try to reset
                    logging.warning(f'partial packet length too long: {self.partial}')
                    self.partial = ''
            else:
                packets.append(packet)

        return packets

    def test(self, seconds):
        """ Reads the serial port for Aeris data """
        for n in range(seconds):
            pks = self.return_packets()
            for p in pks:
                print(p)
            sleep(1)


class Instrument(Aeris):

    newfile = True

    def __init__(self):
        super().__init__()
        self.ssv = SSV(cfg.ssv_add, port=cfg.ssv_port)
        self.ssv.verbose = True

    def save_aeris(self, packet, ssv_position):
        """ Save data packets with SSV postion to a .csv file """
        with open(cfg.aeris_datafile, 'a') as f:
            for p in filter(None, packet):
                p = f'{p},{ssv_position:02d}'
                if self.newfile:
                    f.write('datetime,inlet_num,press_gas,temp_gas,n2o,h2o,co,temp_amb,code,ssv\n')
                    self.newfile = False
                f.write(p+'\n')
                print(p)

    def run(self, seq):
        """ Run a valve sequence. Store data """
        assert isinstance(seq, list)    # seq must be a list()

        for ssv_position, duration in seq:
            self.ssv.go(ssv_position)
            for sec in range(duration):
                pks = self.return_packets()
                self.save_aeris(pks, ssv_position)
                sleep(1)


if __name__ == '__main__':

    opt = argparse.ArgumentParser(description='Aeris N2O/CO instrument.')
    opt.add_argument('-t', action='store', type=int, metavar='SECONDS',
        dest='test', help='Test Aeris. Number of seconds to collect data.')
    options = opt.parse_args()

    if options.test:
        aeris = Aeris()
        aeris.test(options.test)
        quit()

    aeris = Instrument()
    aeris.run(cfg.seq)
