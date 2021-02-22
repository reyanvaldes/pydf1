# Example of how use class to read DF1 protocol (PCCC commands) from Allen Bradley PLC using serial
# Authors:
#  - Jerther Thériault <jtheriault@metalsartigan.com>
#  - Reyan Valdes <rvaldes@itgtec.com>

# Repositories
# Original: https://github.com/metalsartigan/pydf1
# Adapted:

import time
import serial
import sys
import struct

sys.path.append('df1/')
sys.path.append('df1/commands/')
sys.path.append('df1/models/')
sys.path.append('df1/models/exceptions')
sys.path.append('df1/replies/')

from df1_serial_client import Df1SerialClient, TIMER, COUNTER, BIT


client = Df1SerialClient(plc_type='MicroLogix 1000', src=0x0, dst=0x1,
                         port='COM3',
                         baudrate=38400, parity=serial.PARITY_NONE,
                         stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                         timeout=3)
client.connect()

output =0
for i in range(10000):
    print('Running',i+1)
    start_time = time.time()

    # output += 1
    # output = 0 if output>15 else output

    # Write operations
    # client.write_binary(start=0,data=[0b1100])
    # client.write_output(data=[output]) # 0b1101
    # client.write_register(data=[11,25])
    # client.write_float(start=0, data=[11.5,26.4])

    # Reading operations OK
    try:
        print('N7:3-5',    client.read_integer(start=0, total_int=6))  # Read Integers OK
        print('N7:0-2', client.read_integer(start=0, total_int=3))  # Read Integers OK
        print('Timer4:1',  client.read_timer(start=1, category=TIMER.ACC))  # Read Timer OK
        print('Counter5:0',client.read_counter(start=0, category=COUNTER.PRE)) # Read Counter OK
        print('R6:0', client.read_register(start=0, total_int=4))  # Read Registers- CONTROL OK
        print('B3:0', client.read_binary(start=0))  # Read Binary bits words OK
        out0 = client.read_output(start=0, bit=BIT.ALL, total_int=2)
        print('O0:0/1', out0)# , 'bit', client.bit_inspect(out0, BIT.BIT3))  # Read Outputs OK and Bits inspect
        print('I1:0', client.read_input(start=0, bit=BIT.BIT1, total_int=2))  # Read Inputs
        # # Testing
        # print('Float8:0',client.read_float(start=0, total_float=2))  # Read Float
    except Exception as e:
        print('[ERROR] Runtime error has happened',e)
        client.reconnect()
    except KeyboardInterrupt:
        print('Control+C')
        break

    end_time = time.time()
    print('Elapsed(s)', end_time-start_time)
    print('-------------------')

client.close()

print('end testing')

# command1 = client.create_command(Command0FAA, table=0x0, data_to_write=[0x02],
#                                      file_type=FileType.OUT_LOGIC, start=0x00, start_sub=0x00)
#     reply = client.send_command(command1)

# command1 = client.create_command(Command0FA2, bytes_to_read=12, table=0x7,
#                                    file_type=FileType.INTEGER, start=0x00, start_sub=0x00)
#
# command2 = client.create_command(Command0FA2, bytes_to_read=2, table=0x4,
#                                    file_type=FileType.TIMER, start=0x00, start_sub=0x0)


# reply = client.send_command(command1)
# print('N7:0-5', reply.get_data(FileType.INTEGER))

# reply = client.send_command(command2)
# print('Data', reply.get_data(FileType.INTEGER)[0]) # bin(n >> 10)

# reply = client.send_command(command3)
# print('Data', reply.get_data(FileType.INTEGER))

#command = Command0FA2()
# command.init_with_params(src=0x0, dst=0x1, tns=0xe7, bytes_to_read=2, table=0x7,
# #                                file_type=FileType.INTEGER, start=0xfe, start_sub=0xb3)
# ser.write(frame.get_bytes())
# time.sleep(0.01)
#
# response = bytearray()
# while ser.inWaiting() >0:
#     response.append(int.from_bytes(ser.read(1), "little"))
#
# print(response)

# ser.close()




