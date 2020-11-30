#! /usr/bin/env python

import serial
import time
import argparse


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
        return self.aeris.read_all().decode()

    def valid_packet(self, packet):
        """ Criteria for a full data packet from the Aeris instrument.
            A valid packet has 9 cells of data and the first cell is
            exactly 23 characters (MM/DD/YYYY HH:MM:SS.sss) """
        datums = list(filter(None, packet.split(',')))
        if len(datums) != 9 or len(datums[0]) != 23:
            return False
        return True

    def return_packets(self):
        data = self.read_data()
        packets = []
        # parse data packets between \r\n
        for packet in filter(None, data.split('\r\n')):
            if not a.valid_packet(packet):
                # not a complete packet, add next packet to it.
                self.partial = self.partial + packet
                if a.valid_packet(self.partial):
                    packets.append(self.partial)
                    self.partial = ''
                elif len(self.partial) > 90:
                    # something went wrong try to reset
                    self.partial = ''
            else:
                packets.append(packet)

        return packets


if __name__ == '__main__':

    default_port = '/dev/cu.usbserial-1410'
    default_secs = 10

    opt = argparse.ArgumentParser(
        description='Aeris N2O/CO instrument.'
    )
    opt.add_argument('-n', action='store', default=default_secs, type=int,
        dest='seconds',
        help=f'Number of seconds to collect data (default is {default_secs})')
    opt.add_argument('-p', action='store', default=default_port,
        dest='port', help=f'serial port to use (default is {default_port})')

    options = opt.parse_args()

    a = Aeris(port=options.port)

    for n in range(options.seconds):
        pks = a.return_packets()
        for p in pks:
            print(len(p), p)

        time.sleep(1)
