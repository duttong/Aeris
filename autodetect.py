#! /usr/bin/env python
""" Converted to python 3.6.  181018 GSD
    Added Omega temp controllers  190606 GSD
"""

import serial
from time import sleep

READBYTES = 1000
DELAY = 0.05
potential_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3']
all_devices = {'adr2000': None, 'valco': None, 'omega_flow': None, 'omega_temp': None}


class SerialAutoDetect():

    def __init__(self, devices=all_devices):
        self.devices = devices
        self.baud = {'valco': 9600, 'adr2000': 9600, 'omega_flow': 19200, 'omega_temp': 9600}
        self.cmds = {
            'valco': self.cmd_valco,
            'adr2000': self.cmd_adr2000,
            'omega_flow': self.cmd_omega_flowmeter,
            'omega_temp': self.cmd_omega_temp
        }
        self.assign_ports()

    """ Hardcoded commands for each type of device """

    def cmd_valco(self, ser):
        """ Requires a Valco valve on address 1 """
        cmd = '1cp\n'
        ser.write(cmd.encode())
        sleep(DELAY)
        d = ser.read(READBYTES)
        self.devices['valco'] = ser.port if len(d) > 0 else None

    def cmd_adr2000(self, ser):
        ser.write('\rRD\r'.encode())
        sleep(DELAY)
        d = ser.read(READBYTES)
        self.devices['adr2000'] = ser.port if len(d) > 0 else None

    def cmd_omega_flowmeter(self, ser):
        ser.write('\rA\r'.encode())
        sleep(DELAY)
        d = ser.read(READBYTES)
        self.devices['omega_flow'] = ser.port if len(d) > 0 else None

    def cmd_omega_temp(self, ser):
        """ Requires an Omega on address 1 """
        ser.write('*01R01\r'.encode())
        sleep(0.3)      # Omega delay is longer than DELAY
        d = ser.read(READBYTES)
        try:
            # v = d[1:].decode()
            self.devices['omega_temp'] = ser.port if len(d) > 0 else None
        except UnicodeDecodeError:
            self.devices['omega_temp'] = None

    def process_cmds(self, device, ser):
        func = self.cmds[device]
        ser.flushInput()
        sleep(DELAY)
        func(ser)

    def assign_ports(self):
        for port in potential_ports:
            for dev, status in self.devices.items():
                if status is None:
                    try:
                        ser = serial.Serial(port, timeout=DELAY, baudrate=self.baud[dev])
                        self.process_cmds(dev, ser)
                        ser.close()
                    except serial.serialutil.SerialException:
                        print(f'{dev} not found on {port}')


if __name__ == '__main__':

    ''' Here is how to call on a single serial device
    dv = {'valco':None}
    auto = SerialAutoDetect(dv)
    '''
    auto = SerialAutoDetect()
    print(auto.devices)
