#! /usr/bin/env python

import re
import sys
import argparse
import queue
import logging
import serial
from time import sleep, time
from datetime import datetime
from threading import Thread

import autodetect

VERSION = '1.3'
''' Added autodetect.py and removed old autodetect code.  GSD 150417
    Upadated for python 3.6.  Switched from optionparse to argparse.  GSD 181018
'''

DELAYsend = 0.01
DELAYloop = 0.1


class Valco_Valve_Commands:
    """ Commands that work on all Valco valves.

        Not all of the commands are programed.
        See https://www.vici.com/support/tn/tn413.pdf for two position valve
        See https://www.vici.com/support/tn/tn415.pdf for multi-postion valve
        commands.

    """

    def __init__(self, add=None, port=None, baud=9600):
        """ autodetects port only if port option is set to None
            baud = 9600 is the factory default from Valco
        """
        self.baud = baud
        self.port = self.auto(port, 'valco')
        self.ser = self.connect()
        self.add = add

    def auto(self, port, device):
        if port is None:
            auto = autodetect.SerialAutoDetect({device: None})
            if auto.devices[device] is None:
                print(f'Could not deterimine valid serial port for {device}')
                quit()
            print(f'Autodetecting port.\nUsing port: {auto.devices[device]} for {device}')
            return auto.devices[device]
        else:
            return port

    def connect(self):
        """ connect to Valco valves serial port """
        try:
            ser = serial.Serial(self.port, timeout=0.05, baudrate=self.baud,
                bytesize=8, parity='N', stopbits=1)
        except serial.serialutil.SerialException:
            sys.stderr.write(f'Could not connect to serial port: {self.port}\n')
            quit()
        return ser

    def send_cmd(self, add, cmd):
        """ Send a command to valco valve via serial port. """
        if add is None:
            cmd = f'{cmd}\n'
        else:
            cmd = f'{add}{cmd}\n'
        self.ser.write(cmd.encode())
        sleep(DELAYsend)

    def read_cmd(self, bytes=100):
        """ Reads any returned data on the serial port. """
        # sleep(.05)
        r = self.ser.read(bytes)
        self.ser.flushInput()
        try:
            data = r.decode()
        except UnicodeDecodeError:
            data = ''
        return data

    # returns current valve position
    def cp(self, add):
        self.send_cmd(add, 'cp')
        r = self.read_cmd()
        return self.__parse_cp(r)

    # parses cp return into current position of A or B
    def __parse_cp(self, str):
        # cp for GSV
        m = re.search(r'"(\w)"', str)
        if m is None:
            # search for ssv instead
            m = re.search(r'= (\d)', str)
            if m is None:
                return None
        return m.group(1)

    # returns current id or address
    def id(self):
        self.send_cmd(self.add, 'id')
        r = self.read_cmd()
        m = re.search(r'= (\d)', r)
        if m is None:
            return None
        return m.group(1)


class GSV(Valco_Valve_Commands):
    """ Commands specific to 2 position valves, Gas Sample Valve """

    def __init__(self, add, port=None, baud=9600):
        super().__init__(port=port, baud=baud)
        self.add = add
        self.pos = 'Unknown'
        self.verbose = True

    def cp(self):
        """ override the cp method to include updating self.pos """
        self.pos = Valco_Valve_Commands.cp(self, self.add)
        return self.pos

    def tog(self):
        """ Valco 'to' command.  Toggles position. """
        self.send_cmd(self.add, 'to')

    def goa(self):
        """ Go to position A """
        self.send_cmd(self.add, 'goa')
        self.pos = 'A'

    def gob(self):
        """ Go to position B """
        self.send_cmd(self.add, 'gob')
        self.pos = 'B'

    def load(self):
        """ 'load' command is position B """
        self.gob()
        if self.verbose:
            print(f'{datetime.now()} load {self.add}')
            logging.info(f'load {self.add}')

    def inject(self):
        """ 'inject' command is position A """
        self.goa()
        if self.verbose:
            print(f'{datetime.now()} inject {self.add}')
            logging.info(f'inject {self.add}')

    def pos_txt(self):
        """ Returns the valve postion as load/inject instead of A/B """
        if self.pos == 'A':
            return 'inject'
        elif self.pos == 'B':
            return 'load'
        else:
            return 'unknown'

    # re-aligns a valve
    def realign(self):
        self.send_cmd(self.add, 'in')   # initialize
        sleep(DELAYsend)
        for itr in range(6):
            self.tog()
            sleep(2)    # seconds


class SSV(Valco_Valve_Commands):
    """ Commands specific to a multi-position valve, Stream Selection Valve.

        REMOVED: The default is set to an 8 port valve, but can be set with the
        numports variable.

        Changed, 181031 to ask valve for number of ports. GSD
        Added: self.pos 190607 GSD
    """

    def __init__(self, add, port=None, baud=9600):
        super().__init__(port=port, baud=baud)
        self.add = add
        self.pos = -1
        self.numports = self.np()    # num ports on the valve
        self.verbose = True

    def np(self):
        """ Returns number of postions a SSV has. """
        self.send_cmd(self.add, 'np')
        m = re.search(r'= (\d+)', self.read_cmd())
        if m is None:
            sys.stderr.write("Can't determine number of ports on SSV. NP command failed.")
            return 0
        return int(m.group(1))

    def cp(self):
        """ Current valve position """
        try:
            self.pos = int(Valco_Valve_Commands.cp(self, self.add))
        except TypeError:
            self.pos = 0
        return self.pos

    def go(self, position):
        self.send_cmd(self.add, f'go={position}')
        self.pos = int(position)
        if self.verbose:
            print(f'{datetime.now()} SSV{self.add} to {position}')
            logging.info(f'SSV{self.add} to {position}')

    def step(self):
        """ Step valve one postion forward. """
        cur = self.cp()
        if cur is None:
            sys.stderr.write(f'Unknown SSV position, address = {self.add}\n')
            return
        new = int(cur) + 1
        new = 1 if new > self.numports else new
        self.go(new)
        self.pos = new

    def home(self):
        """ Return valve to postion 1 dubbed 'home' """
        self.go(1)
        self.pos = 1


class Valves(Valco_Valve_Commands):
    """ Function that apply to many valves. """

    def __init__(self, port=None):
        super().__init__(port=port)
        self.positions = dict()

    def scan(self, adds):
        """ Scans a list of addresses for valves, returns positions """
        loc = [self.cp(id) for id in adds]
        self.positions = dict(zip(adds, loc))
        return self.positions


class Driver(Thread):
    """ threaded driver for all Valco valves attached to vport
        ssv_ids: A list of IDs for multi-position valves
        gsv_ids: A list of IDs for two-position valves
        loop_t: Number of seconds in a loop
        vport: The serial port the valves are hooked to.
    """

    def __init__(self, ssv_ids, gsv_ids, loop_t=1, vport=None):
        Thread.__init__(self)
        self.gsv_ids = gsv_ids
        self.ssv_ids = ssv_ids
        self.loop_t = loop_t
        self.pos = []
        self.GSVs = []
        self.SSVs = []
        self.job = queue.Queue()

        if len(self.gsv_ids + self.ssv_ids) == 0:
            print('No Valco valve addresses defined.')
            return

        Vs = Valves(port=vport)

        # list of valves that are online
        self.online = Vs.scan(self.ssv_ids + self.gsv_ids)
        self.pos = self.online.copy()

        # create valve instances
        self.GSVs = [GSV(i, port=vport) for i in self.gsv_ids]
        self.SSVs = [SSV(i, port=vport) for i in self.ssv_ids]

    # toggles GSV postion
    def tog(self, id):
        if self.pos[id] == 'A':
            self.pos[id] = 'B'
        elif self.pos[id] == 'B':
            self.pos[id] = 'A'
        else:
            pass
        self.GSVs[self.gsv_ids.index(id)].tog()

    # GSV load position
    def load(self, id):
        self.pos[id] = 'B'
        self.GSVs[self.gsv_ids.index(id)].gob()

    # GSV inject position
    def inject(self, id):
        self.pos[id] = 'A'
        self.GSVs[self.gsv_ids.index(id)].goa()

    # FM GSV calg (cal gas to gc) position
    def calg(self, id):
        self.pos[id] = 'B'
        self.GSVs[self.gsv_ids.index(id)].gob()

    # FM GSV  korg (air cor gas to gc)  position
    def korg(self, id):
        self.pos[id] = 'A'
        self.GSVs[self.gsv_ids.index(id)].goa()

    # returns position full text
    def pos_full(self, id):
        if id == 3:
            if self.pos[id] == 'B':
                return "CalGas"
            elif self.pos[id] == 'A':
                return "KorGas"
            else:
                return "Unknown"
        else:
            if self.pos[id] == 'B':
                return "Load"
            elif self.pos[id] == 'A':
                return "Inject"
            else:
                return "Unknown"

    def run(self):
        """ Called with thread start instance
            Routine will loop through every loop_t seconds and record the current postions
            of all of the valves while checking to see if any tasks are in the queue to be
            operated upon.
        """
        t = time()
        while True:
            for n, id in enumerate(self.gsv_ids):
                if self.online.get(id) is not None:
                    self.pos[id] = self.GSVs[n].cp()
                    # print self.pos[id]
                self.__tasks()
                sleep(DELAYloop)
            for n, id in enumerate(self.ssv_ids):
                if self.online.get(id) is not None:
                    try:
                        self.pos[id] = self.SSVs[n].cp()    # FM removed int()  Error trapping probably not needed as in GSV section
                    except ValueError:
                        self.pos[id] = None
                        print('ssv cp trapped Value error')
                self.__tasks()
                sleep(DELAYloop)

            # wait until near the end of loop_t while still checking the task queue
            while self.loop_t - (time() - t) > DELAYloop*2:     # *2 added 190812 GSD
                self.__tasks()
                sleep(DELAYloop)
            tsleep = self.loop_t - (time() - t)
            if tsleep < 0.0:
                sys.stderr.write(f'Error  tsleep = {tsleep} ')
            else:
                # wait the remaining time
                sleep(self.loop_t - (time() - t))

            t = time()

    def __tasks(self):
        """ Possible job taskes in queue. """
        verbose = True
        if self.job.qsize() > 0:
            try:
                id, cmd = self.job.get()
            except ValueError:
                return

            cmd = cmd.lower()

            # GSV commands
            if cmd == 'tog':
                self.tog(id)
            elif cmd == 'gob' or cmd == 'load' or cmd == 'calg':
                if cmd == 'calg':
                    print('GSV id={0} cal push gas'.format(id))
                elif verbose:
                    print('GSV id={0} loading'.format(id))
                self.load(id)
            elif cmd == 'goa' or cmd == 'inject' or cmd == 'korg':
                if cmd == 'korg':
                    print('GSV id={0} aircore gas'.format(id))
                elif verbose:
                    print('GSV id={0} injecting'.format(id))
                self.inject(id)

            # SSV Commands
            elif cmd == 'step':
                self.SSVs[self.ssv_ids.index(id)].step()
                if verbose:
                    print('Step SSV')
            elif cmd == 'home':
                self.SSVs[self.ssv_ids.index(id)].home()
                if verbose:
                    print('Home SSV')
            elif cmd[0:2] == 'go':
                if verbose:
                    print('SSV to {0}'.format(cmd[2:]))
                self.SSVs[self.ssv_ids.index(id)].go(int(cmd[2:]))

            elif cmd == 'quit':
                quit()
            self.__tasks()


if __name__ == '__main__':

    opt = argparse.ArgumentParser(
        description='Valco valve driver.'
    )
    opt.add_argument('-c', action='store',
        dest='command', help='command string to send to address')
    opt.add_argument('--align', action='store',
        dest='add', help='align the valve position')
    opt.add_argument('--scan', action='store_true',
        dest='scan', help='scan for valves')
    opt.add_argument('-p', action='store',
        dest='port', help='serial port to use (default is autodetect)')

    options = opt.parse_args()

    if options.command:
        v = Valco_Valve_Commands(port=options.port)
        v.send_cmd(None, options.command)
        sleep(0.2)
        print(v.read_cmd(2048))

    if options.add:
        v = GSV(options.add, port=options.port)
        v.realign()
        quit()

    if options.scan:
        print('Scaning for valves:')
        t = Valves(port=options.port)
        print(t.scan(range(10)))
        print('Valve addresses with their current positions.')
        quit()
