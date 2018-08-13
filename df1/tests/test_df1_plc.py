import socket
import time
import unittest

from mock import patch

from models import Df1Plc
from models.exceptions import SendQueueOverflowError
""" Apparemment on peut pas patcher socket.send et socket.recv quand on debug..."""


class TestDf1Plc(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.plc = Df1Plc()
        self.plc.force_one_socket_thread_loop = True
        self.received_data = None
        self.plc_has_disconnected = False
        self.plc.bytes_received.append(self._receive_data)
        self.plc.disconnected.append(self._disconnected)

    def tearDown(self):
        super().tearDown()
        self.plc.close()

    def _receive_data(self, buffer):
        self.received_data = buffer

    def _disconnected(self):
        self.plc_has_disconnected = True

    @patch.object(Df1Plc, '_socket_recv')
    @patch.object(socket.socket, 'close')
    @patch.object(socket.socket, 'connect')
    @patch.object(Df1Plc, '_socket_send')
    def test_send_disconnected(self, mock_send, *args):
        self.plc.connect('127.0.0.1', 666)
        self.plc.close()
        for i in range(4):
            self.plc.send_bytes(bytes([i]))
        self.plc.connect('127.0.0.1', 666)
        self.plc.close()
        self.assertEqual(4, mock_send.call_count)
        for i in range(4):
            first_positional_argument_after_self = mock_send.mock_calls[i][1][0]
            self.assertEqual(bytes([i]), first_positional_argument_after_self)

    @patch.object(socket.socket, 'close')
    @patch.object(Df1Plc, '_socket_recv')
    @patch.object(Df1Plc, '_socket_send')
    @patch.object(socket.socket, 'connect')
    def test_send_disconnected_overflow(self, *args):
        self.plc.connect('127.0.0.1', 666)
        self.plc.close()
        for i in range(100):
            self.plc.send_bytes(bytes([i]))
        with self.assertRaises(SendQueueOverflowError):
            self.plc.send_bytes(bytes([99]))

    @patch.object(Df1Plc, '_socket_recv')
    @patch.object(socket.socket, 'close')
    @patch.object(Df1Plc, '_socket_send')
    @patch.object(socket.socket, 'connect')
    def test_send_bytes(self, mock_connect, mock_send, mock_close, mock_recv):
        self.plc.force_one_queue_send = True
        mock_recv.return_value = bytes()
        self.plc.connect('127.0.0.1', 666)
        self.plc.send_bytes(bytes([1, 2, 3, 4, 5]))
        self.plc.close()
        mock_connect.assert_called_with(('127.0.0.1', 666))
        mock_send.assert_called_with(bytes([1, 2, 3, 4, 5]))
        mock_close.assert_called()
        self.assertIsNone(self.received_data)

    @patch.object(socket.socket, 'close')
    @patch.object(socket.socket, 'connect')
    @patch.object(Df1Plc, '_socket_recv')
    def test_receive_bytes(self, mock_recv, *args):
        expected = bytes([1, 2, 3, 4, 5])
        mock_recv.return_value = expected
        self.plc.connect('127.0.0.1', 666)
        self.plc.close()
        self.assertEqual(expected, self.received_data)

    @patch.object(time, 'sleep')
    @patch.object(socket.socket, 'close')
    @patch.object(socket.socket, 'connect')
    def test_connection_refused(self, mock_connect, *args):
        mock_connect.side_effect = ConnectionError()
        self.plc.connect('127.0.0.1', 666)
        self.plc.close()
        mock_connect.assert_called()

    @patch.object(time, 'sleep')
    @patch.object(socket.socket, 'close')
    @patch.object(socket.socket, 'connect')
    def test_connection_timeout(self, mock_connect, *args):
        mock_connect.side_effect = socket.timeout()
        self.plc.connect('127.0.0.1', 666)
        self.plc.close()
        mock_connect.assert_called()

    @patch.object(socket.socket, 'connect')
    @patch.object(Df1Plc, '_socket_recv')
    def test_connection_dropped(self, mock_recv, *args):
        self.plc.connect('127.0.0.1', 666)
        mock_recv.return_value = bytes()
        self.plc.close()
        self.assertTrue(self.plc_has_disconnected)
