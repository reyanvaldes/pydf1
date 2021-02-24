44
# Example of how use class to read DF1 protocol (PCCC commands) from Allen Bradley PLC using serial/TCP adapter
# Authors:
#  - Jerther Thériault <jtheriault@metalsartigan.com>
#  - Reyan Valdes <rvaldes@itgtec.com>

# Repositories
# Original: https://github.com/metalsartigan/pydf1
# Adapted: https://github.com/reyanvaldes/pydf1

import time
import sys

from df1.models.df1_base import TIMER, COUNTER, BIT
from df1.models.df1_tcp_client import Df1TCPClient
import struct

client = Df1TCPClient(ip_address ='192.168.0.7', ip_port =44818, plc_type='MicroLogix 1000', src=0x0, dst=0x1,
                         timeout=2)
client.connect()

# output =0
for i in range(10000000):
    # print('Running',i+1)
    start_time = time.time()

    # output += 1
    # output = 0 if output>15 else output
    try:
    # Write operations
        # client.write_binary(start=0,data=[0b1100])
        # client.write_output(data=[output]) # 0b1101
        # client.write_register(data=[11,25])
        # client.write_float(start=0,data=[51.4, 600.5])

        # Reading operations OK

        print('N7:3-5',    client.read_integer(start=0, total_int=6))  # Read Integers OK
        print('N7:0-2', client.read_integer(start=0, total_int=3))  # Read Integers OK
        print('Timer4:1',  client.read_timer(start=0, category=TIMER.ACC))  # Read Timer OK
        print('Counter5:0',client.read_counter(start=0, category=COUNTER.PRE)) # Read Counter OK
        print('R6:0', client.read_register(start=0, total_int=4))  # Read Registers- CONTROL OK
        print('B3:0', client.read_binary(start=0))  # Read Binary bits words OK
        out0 = client.read_output(start=0, bit=BIT.ALL, total_int=1)
        print('O0:0', out0)  # Read Outputs OK and Bits inspect
        print('I1:0', client.read_input(start=0, bit=BIT.BIT1, total_int=2))  # Read Inputs
        # Testing
        # print('Float8:0',client.read_float(start=0, total_float=2))  # Read Float
        # except Exception as e:
        #     print('[ERROR] Runtime error has happened',e)
        end_time = time.time()
        print('Elapsed(s)', end_time-start_time)
        # print('-------------------')
    except Exception as e:
        print('[WARN] Runtime error has happened',e)
        client.reconnect()

    except KeyboardInterrupt:
        print('Control+C')
        break

client.close()

print('end testing, reconnect', client.reconnect_total())




