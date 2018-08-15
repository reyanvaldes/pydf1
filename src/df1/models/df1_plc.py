import select
import socket
import time
from collections import deque
from threading import Thread

from . import BasePlc
from .exceptions import SendQueueOverflowError

BUFFER_SIZE = 4096
RECEIVE_TIMEOUT = 1
CONNECT_TIMEOUT = 5
SEND_QUEUE_SIZE = 100


class Df1Plc(BasePlc):
    def __init__(self):
        super().__init__()
        self._socket_thread = None
        self._loop = False
        self._address = None
        self._connected = False
        self._plc_socket = None
        self.force_one_socket_thread_loop = False
        self.force_one_queue_send = False
        self.send_queue = deque()

    def connect(self, address, port):
        if not self._socket_thread:
            self._address = (address, port)
            self._loop = True
            self._socket_thread = Thread(target=self._socket_loop, name="Socket thread")
            self._socket_thread.start()

    def close(self):
        if self._socket_thread:
            self._loop = False
            self._socket_thread.join()
            self._socket_thread = None

    def send_bytes(self, buffer: bytes):
        if len(self.send_queue) >= SEND_QUEUE_SIZE:
            raise SendQueueOverflowError()
        else:
            self.send_queue.append(buffer)

    def _socket_loop(self):
        while self._loop or self.force_one_socket_thread_loop or self.force_one_queue_send:
            self.force_one_socket_thread_loop = False
            if not self._connected:
                self._create_connected_socket()
            if self._connected:  # reevaluate after connection
                while self.send_queue:
                    buffer = self.send_queue.popleft()
                    self._socket_send(buffer)
                    self.force_one_queue_send = False
                self._receive_bytes()
        self._connected = False
        if self._plc_socket:
            self._plc_socket.close()

    def _socket_send(self, buffer):  # pragma: nocover
        """To enable mock.patch on send() without hurting the debugger."""
        self._plc_socket.send(buffer)

    def _socket_recv(self):  # pragma: nocover
        """To enable mock.patch on recv() without hurting the debugger."""
        return self._plc_socket.recv(BUFFER_SIZE)

    def _receive_bytes(self):
        in_sockets, out_sockets, ex = select.select([self._plc_socket], [], [], RECEIVE_TIMEOUT)
        if in_sockets:
            buffer = self._socket_recv()
            if buffer:
                self._on_bytes_received(buffer)
            else:
                self._plc_socket.close()
                self._connected = False
                self._on_disconnected()

    def _create_connected_socket(self):
        plc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        plc_socket.settimeout(CONNECT_TIMEOUT)
        try:
            plc_socket.connect(self._address)
            self._connected = True
            self._plc_socket = plc_socket
        except (ConnectionError, socket.timeout):
            plc_socket.close()
            time.sleep(1)

