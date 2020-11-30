#! /usr/bin/env python

import serial
import time
import argparse
import logging

from valco import SSV


class Aeris:

    partial = ''

    def __init__(self, port='/dev/cu.usbserial-1410'):
        self.port = port
        self.aeris = self.aeris_connect()

    def aeris_connect(self):
        """ Setup serial connection to Aeris N2O/CO instrument """
        ser = serial.Serial(self.port, timeout=0.05, baudrate=9600)
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
                    logging.warning(f'partial packet lenght too long: {self.partial}')
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
            time.sleep(1)


if __name__ == '__main__':

    default_port = '/dev/cu.usbserial-1410'

    opt = argparse.ArgumentParser(description='Aeris N2O/CO instrument.')
    opt.add_argument('-p', action='store', default=default_port,
        dest='port', help=f'serial port to use (default is {default_port})')
    opt.add_argument('-t', action='store', type=int, metavar='SECONDS',
        dest='test', help='Test Aeris. Number of seconds to collect data.')
    options = opt.parse_args()

    # instance for instrument
    aeris = Aeris(port=options.port)

    if options.test:
        aeris.test(options.test)
        quit()

    valve = SSV(port='/dev/cu.usbserial')

    iter = 5
    seq = [1, 2, 3, 4] * iter      # valve postions
    seq_dur = 60    # seconds
