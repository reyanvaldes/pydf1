
import time
import sys
sys.path.append('df1/')
sys.path.append('df1/commands/')
sys.path.append('df1/models/')
sys.path.append('df1/models/exceptions')
sys.path.append('df1/replies/')

from df1_tcp_client import Df1TCPClient
from df1_serial_client import Df1SerialClient
from df1_base import TIMER, COUNTER, BIT
from threading import Thread
import serial

def read_tcp():
    client = Df1TCPClient(ip_address ='192.168.10.23', ip_port =44818, plc_type='MicroLogix 1000', src=0x0, dst=0x1,
                             timeout=2)
    client.connect()

    for i in range(100):
        print('TCP Running',i+1)
        start_time = time.time()

        try:
            print('N7:3-5', client.read_integer(start=0, total_int=6))  # Read Integers OK
            out0 = client.read_output(start=0, bit=BIT.ALL, total_int=2)
            print('O0:0/3', out0)  # Read Outputs OK and Bits inspect
            print('I1:0', client.read_input(start=0, bit=BIT.BIT1, total_int=2))  # Read Inputs
            end_time = time.time()
            print('TCP Elapsed(s)', end_time - start_time)
            # print('-------------------')
        except Exception as e:
            print('[WARN] Runtime error has happened', e)
            client.reconnect()
        except KeyboardInterrupt:
            print('Control+C')
            break

    client.close()

    print('end TCP testing')


def read_serial():
    client = Df1SerialClient(plc_type='MicroLogix 1000', src=0x0, dst=0x1,
                             port='COM3',
                             baudrate=38400, parity=serial.PARITY_NONE,
                             stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                             timeout=3)
    client.connect()

    for i in range(100):
        print('Serial Running', i + 1)
        start_time = time.time()

        try:
            print('N7:3-5', client.read_integer(start=0, total_int=6))  # Read Integers OK
            out0 = client.read_output(start=0, bit=BIT.ALL, total_int=2)
            print('O0:0/3', out0)  # Read Outputs OK and Bits inspect
            print('I1:0', client.read_input(start=0, bit=BIT.BIT1, total_int=2))  # Read Inputs
            end_time = time.time()
            print('Serial Elapsed(s)', end_time - start_time)
            # print('-------------------')
        except Exception as e:
            print('[WARN] Runtime error has happened', e)
            client.reconnect()
        except KeyboardInterrupt:
            print('Control+C')
            return

    client.close()

    print('end Serial testing')


if __name__ == "__main__":
    try:
        t1 = Thread(target = read_tcp)
        t2 = Thread(target = read_serial)
        t1.setDaemon(True)
        t2.setDaemon(True)
        t1.start()
        t2.start()
        while True:
            time.sleep(1000)
            pass
    except KeyboardInterrupt:
        print('Control+C')