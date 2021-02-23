# DF1

A very basic Allen Bradley DF1 protocol implementation in Python.

### How to use: example 1- Reading TCP using commands

from df1.df1_client import Df1Client
from df1.commands import Command0FA2
from df1.file_type import FileType

with Df1Client(src=0x0, dst=0x1) as client:
    client.connect('192.168.0.32', 10232)
    command = client.create_command(Command0FA2, table=43, start=245, bytes_to_read=10, file_type=FileType.INTEGER)
    reply = client.send_command(command)
    print(reply.get_data(FileType.INTEGER))


### How to use: example 2- using wrapper functions for writing/reading TCP

see https://github.com/reyanvaldes/pydf1/blob/master/tests/df1/df1_tcp_serial_example.py

### How to use: example 3- using wrapper functions for writing/reading serial

See https://github.com/reyanvaldes/pydf1/blob/master/tests/df1/df1_serial_example.py

