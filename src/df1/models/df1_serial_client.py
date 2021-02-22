# -*- coding: utf-8 -*-

# Class for Serial Client to read DF1 protocol (PCCC commands) from Allen Bradley PLC using serial  adapter
# Authors:
#  - Jerther Thériault <jtheriault@metalsartigan.com>
#  - Reyan Valdes <rvaldes@itgtec.com>

# Repositories
# Original: https://github.com/metalsartigan/pydf1
# Adapted:  https://github.com/reyanvaldes/pydf1

"""
 Example of using:
import time
from df1_tcp_client import Df1TCPClient
from df1_base import TIMER, COUNTER, BIT
from df1_serial_client import Df1SerialClient, TIMER, COUNTER, BIT


client = Df1SerialClient(plc_type='MicroLogix 1000', src=0x0, dst=0x1,
                         port='COM3',
                         baudrate=19200, parity=serial.PARITY_NONE,
                         stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                         timeout_sec=3)
client.connect()
try:
    print('N7:3-5', client.read_integer(start=0, total_int=3))  # Read Integers
except Exception as e:
    print('[WARN] Runtime error has happened',e)
    client.reconnect()
client.close()
"""

import serial
from df1.models.df1_base import Df1BaseClient, TIMER, COUNTER, BIT
from df1.models.df1_serial_plc import Df1SerialPlc


SEND_SEQ_SLEEP_TIME = 0.001  # magic with this sleep time to get faster processing in the Send Command sequence
TIMEOUT_READ_MESSAGE = 3  # seconds

# Df1SerialClient allows read or write using PCCC commands
# Behind the scene is using for reading: Cmd=0F/Fnc=A2, for writing: Cmd=0F/Fnc=AA
# See manual 7-3- Communication Commands
# PLC supported: Micrologix 1000, SLC 500, SLC 5/03, SLC 5/04, PLC-5
# note: the parsing of data is done in class Reply4f (reply_4.py)

class Df1SerialClient(Df1BaseClient):
    def __init__(self, plc_type='MicroLogix 1000', src=0, dst=1,
                 port='/dev/ttyS0', baudrate=19200, parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=3, history_size=20):
        super().__init__(plc_type=plc_type, src=src, dst=dst,
                         seq_sleep_time=SEND_SEQ_SLEEP_TIME, timeout_read_msg=TIMEOUT_READ_MESSAGE,
                         timeout=timeout, history_size=history_size)
        self._port = port
        self._baudrate = baudrate
        self._parity = parity
        self._stopbits = stopbits
        self._bytesize = bytesize
        self._plc = Df1SerialPlc()
        self._plc.bytes_received.append(self._bytes_received)  # set call back


    def connect(self):
        if self._plc_supported:
            return self._plc.open(port=self._port, baudrate=self._baudrate,
                                  parity=self._parity, stopbits=self._stopbits, bytesize=self._bytesize,
                                  timeout=self._timeout)
        else:
            print(f'[ERROR] Cannot open, PLC is not supported, only {PLC_SUPPORTED}')


