# -*- coding: utf-8 -*-
# Class for TCP Client to read DF1 protocol (PCCC commands) from Allen Bradley PLC using serial/TCP adapter
# Authors:
#  - Jerther Thériault <jtheriault@metalsartigan.com>
#  - Reyan Valdes <rvaldes@itgtec.com>

# Repositories
# Original: https://github.com/metalsartigan/pydf1
# Adapted:

from df1_base import Df1BaseClient
from models import Df1TCPPlc

"""
 Example of using:
import time
from df1_tcp_client import Df1TCPClient
from df1_base import TIMER, COUNTER, BIT
client = Df1TCPClient(ip_address ='192.168.10.23', ip_port =44818, plc_type='MicroLogix 1000', src=0x0, dst=0x1,
                         timeout=2)
client.connect()
try:
    print('N7:3-5', client.read_integer(start=0, total_int=3))  # Read Integers
    print('N7:3-5', client.read_integer(start=0, total_int=3))  # Read Integers
except Exception as e:
    print('[WARN] Runtime error has happened',e)
    client.reconnect()      
client.close()
"""



TIMEOUT_READ_MESSAGE = 0.5  # seconds
# Magic number with this sleep time to get faster processing in the Send Command sequence
SEND_SEQ_SLEEP_TIME = 0.0000000001

# IMPORTANT CONFIGURATION FOR TCP-SERIAL ADAPTER:
# The Ethernet -Serial adapter has to be configured as following:
# TCP: Work Mode= TCP Server, IP, Port, UART packet Time =40 ms, UART packet length =0
# RS232: Baud rate, Data size, Parity, Stop bits, Flow Control = None that match PLC


class Df1TCPClient (Df1BaseClient):
    def __init__(self, ip_address='127.0.0.1', ip_port=44818,
                 plc_type= 'MicroLogix 1000', src=0x0, dst=0x1, timeout=3, history_size=30):
        super().__init__(plc_type=plc_type, src=src, dst=dst,
                         seq_sleep_time=SEND_SEQ_SLEEP_TIME, timeout_read_msg=TIMEOUT_READ_MESSAGE,
                         timeout=timeout, history_size=history_size)
        self._ip_address = ip_address
        self._ip_port = ip_port
        self._plc = Df1TCPPlc()
        self._plc.bytes_received.append(self._bytes_received)

    def connect(self):
        if self._plc_supported:
            return self._plc.connect(address =self._ip_address, port= self._ip_port, timeout = self._timeout)
        else:
            print(f'[ERROR] Cannot open, PLC is not supported, only {PLC_SUPPORTED}')

