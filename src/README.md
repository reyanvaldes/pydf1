# DF1

A very basic Allen Bradley DF1 protocol implementation in Python.

### How to use: example 1- Reading TCP using commands
```python
from df1.df1_client import Df1Client
from df1.commands import Command0FA2
from df1.file_type import FileType

with Df1Client(src=0x0, dst=0x1) as client:
    client.connect('192.168.0.32', 10232)
    command = client.create_command(Command0FA2, table=43, start=245, bytes_to_read=10, file_type=FileType.INTEGER)
    reply = client.send_command(command)
    print(reply.get_data(FileType.INTEGER))
```

### How to use: example 2- using wrapper functions for writing/reading TCP

```python
import time
import sys
from df1.models.df1_base import TIMER, COUNTER, BIT
from df1.models.df1_tcp_client import Df1TCPClient
import struct

client = Df1TCPClient(ip_address ='192.168.10.23', ip_port =44818, plc_type='MicroLogix 1100', src=0x0, dst=0x1,timeout=2)
client.connect()

client.write_binary(start=0,data=[0b1100])
client.write_output(data=[output]) # 0b1101
client.write_register(data=[11,25])
client.write_float(start=0, data=[11.5,26.4])

print('N7:3-5',    client.read_integer(start=0, total_int=6))  # Read Integers 
print('N7:0-2', client.read_integer(start=0, total_int=3))  # Read Integers 
print('Timer4:1',  client.read_timer(start=0, category=TIMER.ACC))  # Read Timer 
print('Counter5:0',client.read_counter(start=0, category=COUNTER.PRE)) # Read Counter 
print('R6:0', client.read_register(start=0, total_int=4))  # Read Registers- CONTROL 
print('B3:0', client.read_binary(start=0))  # Read Binary bits words 
out0 = client.read_output(start=0, bit=BIT.ALL, total_int=1) # Can use specific bit like BIT.BIT3
print('O0:0', out0)  # Read Outputs OK and Bits inspect
print('I1:0', client.read_input(start=0, bit=BIT.BIT1, total_int=2))  # Read Inputs
print('Float8:0',client.read_float(start=0, total_float=2))  # Read Float (if PLC support)

client.close()

print('end testing')
```

### How to use: example 3- using wrapper functions for writing/reading serial

```python
import time
import serial

from df1.models.df1_serial_client import Df1SerialClient
from df1.models.df1_base import TIMER, COUNTER, BIT

client = Df1SerialClient(plc_type='MicroLogix 1100', src=0x0, dst=0x1,port='COM3',baudrate=19200, parity=serial.PARITY_NONE, 
		stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,timeout=3)
client.connect()

client.write_binary(start=0,data=[0b1100])
client.write_output(data=[output]) # 0b1101
client.write_register(data=[11,25])
client.write_float(start=0, data=[11.5,26.4])

print('N7:3-5',    client.read_integer(start=0, total_int=6))  # Read Integers 
print('N7:0-2', client.read_integer(start=0, total_int=3))  # Read Integers 
print('Timer4:1',  client.read_timer(start=1, category=TIMER.ACC))  # Read Timer 
print('Counter5:0',client.read_counter(start=0, category=COUNTER.PRE)) # Read Counter 
print('R6:0', client.read_register(start=0, total_int=4))  # Read Registers- CONTROL 
print('B3:0', client.read_binary(start=0))  # Read Binary bits words 
out0 = client.read_output(start=0, bit=BIT.ALL, total_int=1)  # Can use specific bit like BIT.BIT3
print('O0:0/1', out0)# , 'bit', client.bit_inspect(out0, BIT.BIT3))  # Read Outputs OK and Bits inspect
print('I1:0', client.read_input(start=0, bit=BIT.BIT1, total_int=2))  # Read Inputs
print('Float8:0',client.read_float(start=0, total_float=2))  # Read Float

client.close()

print('end testing')
```
