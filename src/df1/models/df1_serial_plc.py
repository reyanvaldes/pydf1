# -*- coding: utf-8 -*-

# Class for PLC Serial to read DF1 protocol (PCCC commands) from Allen Bradley PLC using serial  adapter
# Authors:
#  - Jerther Thériault <jtheriault@metalsartigan.com>
#  - Reyan Valdes <rvaldes@itgtec.com>

# Repositories
# Original: https://github.com/metalsartigan/pydf1
# Adapted:  https://github.com/reyanvaldes/pydf1

import select
import socket
import errno
import threading
import time
from collections import deque
from threading import Event, Thread

from df1.models.base_plc import BasePlc
from df1.models.exceptions import SendQueueOverflowError, ThreadError
import serial

BUFFER_SIZE = 4096
WRITE_TIMEOUT = 0.00001
INTERCHAR_TIMEOUT = 0.00001
THREAD_START_TIMEOUT = 1
SEND_QUEUE_SIZE = 100


class Df1SerialPlc(BasePlc):
    def __init__(self):
        super().__init__()
        self._connected = False
        self._plc = None
        self._loop_thread = None
        self._loop = False
        self.send_queue = deque()
        self._send_queue_lock = threading.Lock()
        self._ready = Event()
        self._new_bytes_to_send = False
        self.port = 'COM3'
        self.baudrate = 19200
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.bytesize = serial.EIGHTBITS


    def open(self,port='COM3', baudrate=19200, parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=3):
        # print('Opening')
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout
        self._clearing_comm = False
        self._plc = serial.Serial(port=port,baudrate=baudrate,
                                  parity=parity,stopbits=stopbits, bytesize=bytesize,
                                  timeout=self.timeout,write_timeout=WRITE_TIMEOUT, interCharTimeout=INTERCHAR_TIMEOUT)
        self._clear_comm()
        self._connected = self.is_opened()
        self._loop = True
        self._loop_thread = Thread(target=self._serial_loop, name="Serial thread", daemon=True)
        self._loop_thread.start()
        if not self._wait_for_thread():
            raise ThreadError("Socket thread could not be started.")


    def is_opened(self):
        return self._plc.is_open


    def close(self):
        self._close()

    def is_clearing_comm(self):
        return self._clearing_comm

    def clear_comm(self):
        self._clear_comm()

    def is_pending_command(self):
        return len(self.send_queue)>0

    def clear_buffer(self):
        self._plc.flush()
        self._plc.reset_input_buffer()
        self._plc.reset_output_buffer()

    def _wait_for_thread(self):  # pragma: nocover
        return self._ready.wait(THREAD_START_TIMEOUT)


    def _close(self):
        if self._plc:
            # print('Closing')
            self._loop = False
            # self._loop_thread.join()
            self._loop_thread = None


    def send_bytes(self, buffer):
        # self._serial_send(buffer)
        with self._send_queue_lock:
            if len(self.send_queue) >= SEND_QUEUE_SIZE:
                raise SendQueueOverflowError()
            else:
                self.send_queue.append(buffer)
                self._new_bytes_to_send = True

    def _serial_loop(self):
        ready_set = False
        while self._loop:
            if not ready_set:
                self._ready.set()
                self.ready_set = True
            if not self._connected:
                # TODO complete this
                self._plc.open()
            if self._connected:  # reevaluate after connection
                if len(self.send_queue) > 0:
                    self._send_loop()
                self._receive_bytes()

        self._connected = False
        print('[WARN] Exit Serial Loop')
        if self._plc:
            self._close()
            self._plc = None

    def _send_loop(self):
        with self._send_queue_lock:
            buffer = self.send_queue.popleft()
            self._serial_send(buffer)
        self._new_bytes_to_send = False

    def _serial_send(self, buffer):  # pragma: nocover
        # print('send', buffer)
        self._plc.write(buffer)


    def _receive_bytes(self):
        buffer = bytearray()
        try:
            n_in = self._plc.inWaiting()  # check how many bytes are available
            if n_in>0:
                buffer = self._plc.read(n_in) # read all of them
                # print('received', buffer)
                self._on_bytes_received(buffer)  # calling the Call Back function
        except Exception as e:
            # print('Error receiving, port maybe closed')
            pass


    def _sleep(self):  # pragma: nocover
        time.sleep(1)

    def _clear_comm(self): # reset any communication, to make sure is like new start
        print('[WARN] Waiting for clear any comm with PLC...')
        self._clearing_comm = True
        self.clear_buffer()

        time.sleep(1)
        if self.is_opened():
            while self._read_bytes():  # read all bytes coming from PLC in case of response from previous command
                time.sleep(1)
            print('[WARN] Waiting for clear comm- done')
        else:
            print('[WARN] Abort clear comm- It is not connected to the PLC')
        self._clearing_comm = False

    def _write_bytes(self, data):
        # print('write',data)
        self._plc.write (data)

    def _read_bytes(self):
        buffer =bytearray()
        time.sleep(1) #waiting enough time to make sure PLC already respond with something
        n_in = self._plc.inWaiting()  # check how many bytes are available
        while n_in>0:
            buffer.extend(self._plc.read(n_in))  # read all of them
            time.sleep(0.05)
            n_in = self._plc.inWaiting()

        return buffer