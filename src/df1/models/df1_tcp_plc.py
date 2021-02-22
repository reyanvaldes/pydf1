# -*- coding: utf-8 -*-

# Class for PLC to read DF1 protocol (PCCC commands) from Allen Bradley PLC using serial/TCP adapter
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
from socket import SOL_SOCKET, SO_KEEPALIVE, IPPROTO_TCP, TCP_KEEPCNT

from df1.models.base_plc import BasePlc
from df1.models.exceptions import SendQueueOverflowError, ThreadError

RCV_BUFFER_SIZE = 1024
RECEIVE_TIMEOUT = 0.000000001  # This number impact the reading speed, that is why we have it with 0 (0.0000001)
THREAD_START_TIMEOUT = 1
SEND_QUEUE_SIZE = 100

class Df1TCPPlc(BasePlc):
    def __init__(self):
        super().__init__()
        self._socket_thread = None
        self._loop = False
        self._address = None
        self._connected = False
        self._plc_socket = None
        self._timeout = 3
        self.send_queue = deque()
        self._send_queue_lock = threading.Lock()
        self._new_bytes_to_send = False
        self._clearing_comm = False

    def connect(self, address, port, timeout):
        if not self._socket_thread:
            self._address = (address, port)
            self._timeout=timeout
            self._loop = True
            self._socket_thread = Thread(target=self._socket_loop, name="Socket thread", daemon=True)
            self._socket_thread.start()
            if not self._socket_thread.is_alive():
                raise ThreadError("Socket thread could not be started.")
        return True

    def close(self):
        if self._socket_thread:
            self._loop = False
            self._socket_thread.join()
            self._socket_thread = None

    def reconnect(self):
        self.close()
        address.port = self._address
        self.connect(address, port, self._timeout)

    def clear_comm(self):
        self._clear_comm()

    def send_bytes(self, buffer):
        with self._send_queue_lock:
            if len(self.send_queue) >= SEND_QUEUE_SIZE:
                raise SendQueueOverflowError()
            else:
                self.send_queue.append(buffer)
                self._new_bytes_to_send = True

    def is_clearing_comm(self):
        return self._clearing_comm

    def _socket_loop(self):
        self._create_connected_socket()
        self._clear_comm() # clear any previous communication
        while self._loop:  # or self._new_bytes_to_send
            try:
                if self._connected:  # reevaluate after connection
                    self._send_loop()
                    self._receive_bytes()
                else:
                    self._create_connected_socket()
            except Exception as e:
                print('[WARN] Error with socket')
        self._connected = False
        if self._plc_socket:
            self._close_socket(self._plc_socket)
            self._connected = False
            self._on_disconnected()

    def _send_loop(self):
        if len(self.send_queue)>0:
            with self._send_queue_lock:
                # while self.send_queue:
                buffer = self.send_queue.popleft()
                self._socket_send(buffer)
            self._new_bytes_to_send = False

    def _socket_send(self, buffer):  # pragma: nocover
        # print('send',buffer)
        try:
            self._plc_socket.send(buffer)
        except Exception as e:
            print('[Error] Send runtime error',e)

    def _receive_bytes(self, call_back_receiver=True):
        try:
            in_sockets, out_sockets, error_socket = select.select([self._plc_socket], [], [], RECEIVE_TIMEOUT)
            if in_sockets:
                try:
                    buffer = self._plc_socket.recv(RCV_BUFFER_SIZE)
                except socket.error as e:  # TODO: python 3 ConnectionResetError
                    if e.errno == errno.ECONNRESET:
                        buffer = bytearray()
                    else:  # pragma: nocover
                        return []
                if buffer and call_back_receiver:
                    self._on_bytes_received(buffer)
                else:
                    self._close_socket(self._plc_socket)
                    self._connected = False
                    self._on_disconnected()
        except Exception as e:
            print('[Error] Receive socket error')
            self._close_socket(self._plc_socket)
            self._connected = False
            self._on_disconnected()

    def _create_connected_socket(self):
        print('[INFO] Create new Socket to', self._address)
        plc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        plc_socket.settimeout(self._timeout)
        plc_socket.setsockopt(IPPROTO_TCP, TCP_KEEPCNT, 3)  # drop connection after n fails
        try:
            self._connect_socket(plc_socket, self._address)
            self._connected = True
            self._plc_socket = plc_socket
        except (socket.timeout, socket.error):  # TODO: python 3 add ConnectionError
            print('[Error] Socket Comm Error')
            self._connected = False
            self._close_socket(plc_socket)
            self._sleep()

    def _connect_socket(self, plc_socket, address):  # pragma: nocover
        plc_socket.connect(address)

    def _close_socket(self, plc_socket):  # pragma: nocover
        plc_socket.close()

    def _sleep(self):  # pragma: nocover
        time.sleep(0.5)

    # clear any previous communication with the plc, waiting for all bytes are read
    # and plc doesn't send any more data
    def _clear_comm(self):
       self._clearing_comm = True
       while True:  # read all bytes coming from PLC in case of response from previous command
            print('[WARN] Waiting for clear any comm with PLC...')
            try:
                buffer = bytearray()
                time.sleep(1)
                in_sockets, out_sockets, error_socket = select.select([self._plc_socket], [], [], self._timeout)
                if in_sockets:
                    buffer = self._plc_socket.recv(RCV_BUFFER_SIZE)
                print('[WARN] Received Buffer', buffer)
                if len(buffer)==0 or buffer is None:
                    self._clearing_comm = False
                    print('[WARN] Waiting for clear comm- done')
                    return
            except Exception as e:
                self._clearing_comm = False
                return # return when the buffer is empty and got timeout

