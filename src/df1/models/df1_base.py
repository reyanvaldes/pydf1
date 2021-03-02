# -*- coding: utf-8 -*-

# Parent Class to read DF1 protocol (PCCC commands) from Allen Bradley PLC using serial

# The Classes Df1SerialPlc and Df1TCPClient should inherited from this
# Authors:
#  - Jerther Thériault <jtheriault@metalsartigan.com>
#  - Reyan Valdes <rvaldes@itgtec.com>

# Repositories
# Original: https://github.com/metalsartigan/pydf1
# Adapted: https://github.com/reyanvaldes/pydf1

from collections import deque
import random
import threading
import time
from enum import Enum
import struct

from df1.models.base_plc import BasePlc
from df1.models import frame_factory
from df1.models.reply_timeout import ReplyTimeout
from df1.models.base_data_frame import BaseDataFrame
from df1.models.exceptions import SendReceiveError
from df1.models.receive_buffer import ReceiveBuffer
from df1.models.tx_symbol import TxSymbol
from df1.replies import ReplyAck, ReplyNak, ReplyEnq

from df1.commands.commands import Command0FA2, Command0FAA  # Reading/Writing Command
from df1.file_type import FileType

PLC_SUPPORTED = {'MicroLogix 1100', 'MicroLogix 1000', 'SLC 500', 'SLC 5/03', 'SLC 5/04', 'PLC-5'}
SEND_SEQ_SLEEP_TIME = 0.0001  # magic with this sleep time to get faster processing in the Send Command sequence
WAIT_RECONNECT = 1  # Wait few seconds for open after close
EXPECT_MSG_SLEEP_TIME = 0.02 # Sleep time when receiving messages

class TIMER(Enum):
    """ Timer attributes"""
    EN = 0x01  # only the Enable bit
    TI = 0x02  # TI it only
    DN = 0x03  # the Done Bit

    PRE = 0x04  # PRE category
    ACC = 0x05  # ACCumulator

    STATUS = 0x07  # return all status bits (EN, TI, DN)


class COUNTER(Enum):
    """ Counter attributes"""
    CU = 0x01
    CD = 0x02
    DN = 0x03
    OV = 0x04
    UN = 0x05
    UA = 0x06
    PRE = 0x07
    ACC = 0x08
    STATUS = 0x09  # return all status bits (CU,CD,DN,OV,UN,UA)


class BIT(Enum):
    """ BIT attributes"""
    BIT0 = 0x00
    BIT1 = 0x01
    BIT2 = 0x02
    BIT3 = 0x03
    BIT4 = 0x04
    BIT5 = 0x05
    BIT6 = 0x06
    BIT7 = 0x07
    BIT8 = 0x08
    BIT9 = 0x09
    BIT10 = 0x0A
    BIT11 = 0x0B
    BIT12 = 0x0C
    BIT13 = 0x0D
    BIT14 = 0x0E
    BIT15 = 0x0F
    ALL = 0xA0


# Df1SerialClient allows read or write using PCCC commands
# Behind the scene is using for reading: Cmd=0F/Fnc=A2, for writing: Cmd=0F/Fnc=AA
# See manual 7-3- Communication Commands
# PLC supported: Micrologix 1X00 family, SLC 500, SLC 5/03, SLC 5/04, PLC-5
# note: the parsing of data is done in class Reply4f (reply_4.py)

class Df1BaseClient:
    def __init__(self, plc_type='MicroLogix 1000', src=0, dst=1,
                 seq_sleep_time=0.01, timeout_read_msg =0.5, timeout=3, history_size=20):
        self.comm_history = deque(maxlen=history_size)
        self._src = src
        self._dst = dst
        self._plc_type = plc_type
        self._seq_sleep_time = seq_sleep_time
        self._timeout_read_msg = timeout_read_msg
        self._timeout = timeout
        self._plc = BasePlc()  # by default has one because close need it when compile
        self._messages_sink = []
        self._message_sink_lock = threading.Lock()
        self._last_tns = self._get_initial_tns()
        self._ack = ReplyAck()
        self._nak = ReplyNak()
        self._enq = ReplyEnq()
        self._last_response = [TxSymbol.DLE.value, TxSymbol.NAK.value]
        self._receive_buffer = ReceiveBuffer()
        # check the plc type supported, otherwise give a warning message
        self._clear_comm = False
        self._reconnect_count = 0
        self._command_sent = None
        self._message_dropped =0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._plc:
            self._plc.close()

    # Abstract Connect method, customized for each plc type: Serial, TCP
    def connect(self):
        pass

    def reconnect(self):
        try:
            self._reconnect_count += 1
            # clear any previous buffer left just in case to avoid interfere with other command
            self._plc.clear_buffer()
            self.close()
            time.sleep(WAIT_RECONNECT)
            self.connect()

        except Exception as e:
            print('[ERROR] Reconnect Runtime error', e)
        finally:
            self._clear_comm = False

    def reconnect_total(self):
        return self._reconnect_count

    def message_dropped_total(self):
        return self._message_dropped

    def close(self):
        self._plc.close()

    def is_clear_comm(self):
        return self._plc.is_clearing_comm()

    def is_pending_command(self):
        return self._plc.is_pending_command()

    # Write output bits as entire word, it doesn't write specific bit only but the entire word
    # Used for testing reading. Example of use: write_output (data=[0b0011])
    def write_output(self, table=0, start=0, data=[]):
        command1 = self.create_command(Command0FAA, table=table, data_to_write=data,
                                       file_type=FileType.OUT_LOGIC, start=start, start_sub=0x00)
        reply = self.send_command(command1)

    # Write boolean bits as entire word, it doesn't write specific bit only but the entire word
    # Used for testing reading. Example of use: write_bits (data=[0b0011])
    def write_binary(self, table=3, start=0, data=[]):
        command1 = self.create_command(Command0FAA, table=table, data_to_write=data,
                                       file_type=FileType.BIT, start=start, start_sub=0x00)
        reply = self.send_command(command1)

    # Write registers as int
    # Used for testing reading. Example of use: write_register (data=[11])

    def write_register(self, table=6, start=0, data=[]):
        command1 = self.create_command(Command0FAA, table=table, data_to_write=data,
                                       file_type=FileType.CONTROL, start=start, start_sub=0x00)
        reply = self.send_command(command1)

    # Write floating numbers
    # Used for testing reading. Example of use: write_register (data=[50.4, 100.5])
    def write_float(self, table=8, start=0, data=[]):
        bytes_write = bytearray()
        for value in data:
            buffer = bytearray(struct.pack('<f', value)) # get package using little endian format
            bytes_write += buffer

        command1 = self.create_command(Command0FAA, table=table, data_to_write=bytes_write,
                                       file_type=FileType.FLOAT, start=start, start_sub=0x00)
        reply = self.send_command(command1)

    # Reading Functions
    # Read Outputs O1:0/Bit
    # Note: if read more words that plc is supported, will get null as response from PLC
    def read_output(self, file_table=0, start=0, bit=BIT.ALL, total_int=1) -> list():
        command = self.create_command(Command0FA2, bytes_to_read=total_int * 2, table=file_table,
                                      file_type=FileType.OUT_LOGIC, start=start, start_sub=0x00)
        reply = self.send_command(command)
        # Parsing based on the Category
        values = list()
        if bit == BIT.ALL:  # return all integers as shown
            values = reply.get_data(FileType.INTEGER)
        else:  # related individual bits
            for data in reply.get_data(FileType.INTEGER):
                status = data >> bit.value & 1
                values.append(status)

        return values

    # Read Bits I1:0-XX
    def read_input(self, file_table=1, start=0, bit=BIT.ALL, total_int=1) -> list():
        command = self.create_command(Command0FA2, bytes_to_read=total_int * 2, table=file_table,
                                      file_type=FileType.IN_LOGIC, start=start, start_sub=0x00)
        reply = self.send_command(command)
        # Parsing based on the Category
        values = list()
        if bit == BIT.ALL:  # return all integers as shown
            values = reply.get_data(FileType.INTEGER)
        else:  # related individual bits
            for data in reply.get_data(FileType.INTEGER):
                status = data >> bit.value & 1
                values.append(status)

        return values

    # Read Binary B3:0/Bit
    def read_binary(self, file_table=3, start=0, bit=BIT.ALL, total_int=1) -> list():
        command = self.create_command(Command0FA2, bytes_to_read=total_int * 2, table=file_table,
                                      file_type=FileType.BIT, start=start, start_sub=0x00)
        reply = self.send_command(command)
        # Parsing based on the Category
        values = list()
        if bit == BIT.ALL:  # return all integers as shown
            values = reply.get_data(FileType.INTEGER)
        else:  # related individual bits
            for data in reply.get_data(FileType.INTEGER):
                status = data >> bit.value & 1
                values.append(status)

        return values

    # Read Timers T4:XX.DN/.PRE/.ACC,.DN.EN,.DN
    # Timer - Table 4- OK subs:0-STATUS ( .EN,.TI,.DN: data >> 12  ) ,1-PRE,2-ACTUAL,3-ACC

    def read_timer(self, file_table=4, start=0, category=TIMER.ACC, total_int=1) -> list():
        # Based on category determine the Sub
        sub = 0  # are bits .EN, TI, DN, or all of them in Status
        if category == TIMER.PRE:
            sub = 1
        elif category == TIMER.ACC:
            sub = 2
        command = self.create_command(Command0FA2, bytes_to_read=total_int * 2, table=file_table,
                                      file_type=FileType.TIMER, start=start, start_sub=sub)
        reply = self.send_command(command)
        # Parsing based on the Category
        values = list()
        if category in {TIMER.PRE, TIMER.ACC}:  # return all integers as shown
            values = reply.get_data(FileType.INTEGER)
        else:  # related with status or individual bits
            for data in reply.get_data(FileType.INTEGER):
                status = data >> 12  # the result of this are 4 bits on right side EN TI DN XX

                if category == TIMER.EN:
                    status = status >> 3 & 1
                elif category == TIMER.TI:
                    status = status >> 2 & 1
                elif category == TIMER.DN:
                    status = status >> 1 & 1

                values.append(status)

        return values

    # C5:xx.PRE => read_c (start, COUNTER.PRE, total of counters =1) -> list
    # Counter - Table 5- OK subs: 0-STATUS ( (CU,CD,DN,OV,UN,UA) 111111 >> 10), 1- PRE, 2- ACC

    def read_counter(self, file_table=5, start=0, category=COUNTER.ACC, total_int=1) -> list():
        # Based on category determine the Sub
        sub = 0  # are bits  (CU,CD,DN,OV,UN,UA) or all of them in Status
        if category == COUNTER.PRE:
            sub = 1
        elif category == COUNTER.ACC:
            sub = 2
        command = self.create_command(Command0FA2, bytes_to_read=total_int * 2, table=file_table,
                                      file_type=FileType.COUNTER, start=start, start_sub=sub)
        reply = self.send_command(command)
        # Parsing based on the Category
        values = list()
        if category in {COUNTER.PRE, COUNTER.ACC}:  # return all integers as shown
            values = reply.get_data(FileType.INTEGER)
        else:  # related with status or individual bits
            for data in reply.get_data(FileType.INTEGER):
                status = data >> 10  # the result of this are 6 bits on right side EN TI DN XX

                if category == COUNTER.CU:
                    status = status >> 5 & 1
                elif category == COUNTER.CD:
                    status = status >> 4 & 1
                elif category == COUNTER.DN:
                    status = status >> 3 & 1
                elif category == COUNTER.OV:
                    status = status >> 2 & 1
                elif category == COUNTER.UN:
                    status = status >> 1 & 1
                elif category == COUNTER.UA:
                    status = status & 1

                values.append(status)

        return values

    # Read Integers R6:XX
    def read_register(self, file_table=6, start=0, total_int=1) -> list():
        command = self.create_command(Command0FA2, bytes_to_read=total_int * 2, table=file_table,
                                      file_type=FileType.CONTROL, start=start, start_sub=0x00)
        reply = self.send_command(command)
        values = reply.get_data(FileType.INTEGER)

        return values

    # Read Integers N7:XX
    def read_integer(self, file_table=7, start=0, total_int=1) -> list():
        command = self.create_command(Command0FA2, bytes_to_read=total_int * 2, table=file_table,
                                      file_type=FileType.INTEGER, start=start, start_sub=0x00)
        reply = self.send_command(command)
        values = reply.get_data(FileType.INTEGER)

        return values

    # Read Integers F8:XX- TODO
    def read_float(self, file_table=8, start=0, total_float=1) -> list():
        command = self.create_command(Command0FA2, bytes_to_read=total_float * 4, table=file_table,
                                      file_type=FileType.FLOAT, start=start, start_sub=0x00)
        reply = self.send_command(command)
        values = reply.get_data(FileType.FLOAT)

        return values

    # Inspect a bit in a word
    # return 1 or 0
    def bit_inspect (self, value: int, bit: BIT):
        if bit==bit.ALL:
            return value
        else:
            return (value >> bit.value) & 1

    def _get_initial_tns(self):  # pragma: nocover
        return random.randint(0, 0xffff)

    def _get_new_tns(self):
        self._last_tns += 1
        if self._last_tns > 0xffff:
            self._last_tns = 0x0
        return self._last_tns

    def create_command(self, command_type, **kwargs):
        command = command_type()
        command.init_with_params(src=self._src, dst=self._dst, tns=self._get_new_tns(), **kwargs)
        return command

    def wait_while_com_clear(self):
        # While clear any communication wth PLC hold any send command
        # This is kind of interlock when connect don't send any command until comm is clear
        while self.is_clear_comm():
            pass  # just wait
        # clear any previous buffer left just in case to avoid interfere with other command
        self._plc.clear_buffer()

    def wait_no_pending_command(self):
        # Check there is no pending command to avoid conflict with other previous commands
        # make sure only one command is processing at a time
        while self.is_pending_command():
            pass

    def send_command(self, command):
        """Doc page 4-6 Transmitter"""
        # print('Sending Command')
        for __ in range(3):  # 3
            # print('retry')
            # wait for any pending command to avoid conflict with other previous commands
            # make sure only one command is processing at a time
            self.wait_no_pending_command()

            # While clear any communication wth PLC hold any send command
            self.wait_while_com_clear()

            self.comm_history.append({'direction': 'out', 'command': command})

            self._command_sent = command  # record the command sent to compare with the tns of the message received

            self._plc.send_bytes(command.get_bytes())

            retry_send = False
            got_ack = False
            i = 0
            while i < 3:  # 3
                reply = self._expect_message()
                # print('reply',reply, type(reply))
                if type(reply) is ReplyAck:
                    got_ack = True
                    # self._send_ack()  # Added - Send Ack to PLC on time, this allow PLC knows we received the data
                    i = 0
                elif type(reply) is ReplyNak:
                    command.tns = self._get_new_tns()
                    retry_send = True
                elif type(reply) is ReplyTimeout or not reply.is_valid():
                    print('[ERROR] Error send command', reply)
                    if got_ack:
                        self._send_nak()
                    else:
                        self._send_enq()
                    break  # exit retry loop
                elif got_ack:
                    # validate if this reply correspond to the command using transaction number (TNS),
                    # otherwise drop it and keep trying
                    if self._command_sent.tns == reply.tns:  # Important to check the transaction #, otherwise drop it
                        return reply
                    else:
                        # drop this message and Starting all over again
                        # This could happened or either bad response from PLC or something happened with the queue
                        self._message_dropped += 1
                        print(f'[ERROR]**** Message dropped- CMD TNS:{self._command_sent.tns} Reply TNS:{reply.tns} ')

                i += 1
                if self._seq_sleep_time>0:
                    time.sleep(self._seq_sleep_time)

            if not retry_send:
                raise SendReceiveError()

        raise SendReceiveError()

    def _bytes_received(self, buffer):
        """Doc page 4-8"""
        self._receive_buffer.extend(buffer)
        for full_frame in self._receive_buffer.pop_left_frames():
            self._process_frame_buffer(full_frame)

    def _process_frame_buffer(self, buffer):
        message = frame_factory.parse(buffer)
        self.comm_history.append({'direction': 'in', 'command': message})
        if type(message) == ReplyEnq:
            last_response_buffer = bytearray(self._last_response)
            self.comm_history.append({'direction': 'out', 'command': frame_factory.parse(last_response_buffer)})
            self._plc.send_bytes(last_response_buffer)
        elif issubclass(type(message), BaseDataFrame):
            if message.is_valid():
                self._send_ack()   # let know PLC we received the message and it is valid
                # validate if this reply correspond to the command using transaction number (TNS),
                # otherwise drop it
                if self._command_sent.tns == message.tns:
                    with self._message_sink_lock:
                        self._messages_sink.append(message)
            else:
                self._send_nak()
        else:
            with self._message_sink_lock:
                self._messages_sink.append(message)
            self._last_response = [TxSymbol.DLE.value, TxSymbol.NAK.value]

    def _expect_message(self):
        startTime = time.time()
        while (True):
            with self._message_sink_lock:
                if self._messages_sink:
                    return self._messages_sink.pop(0)
                endTime = time.time()
                if endTime - startTime > self._timeout_read_msg:
                    break
            time.sleep(EXPECT_MSG_SLEEP_TIME)
        return ReplyTimeout()

    def _send_ack(self):
        # print('send ACK')
        self._last_response = [TxSymbol.DLE.value, TxSymbol.ACK.value]
        self.comm_history.append({'direction': 'out', 'command': self._ack})
        self._plc.send_bytes(self._ack.get_bytes())

    def _send_nak(self):
        # print('send NAK')
        self._last_response = [TxSymbol.DLE.value, TxSymbol.NAK.value]
        self.comm_history.append({'direction': 'out', 'command': self._nak})
        self._plc.send_bytes(self._nak.get_bytes())

    def _send_enq(self):
        # print('send ENQ')
        self.comm_history.append({'direction': 'out', 'command': self._enq})
        self._plc.send_bytes(self._enq.get_bytes())
