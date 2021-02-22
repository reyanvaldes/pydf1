# -*- coding: utf-8 -*-

from df1.models.base_data_frame import BaseDataFrame
from df1.file_type import FileType
import struct

# Do the parsing of the raw data read
class Reply4f(BaseDataFrame):
    def __init__(self, **kwargs):
        super(Reply4f, self).__init__(**kwargs)

    def init_with_params(self, dst, src, tns, data):
        super(Reply4f, self).init_with_params(src=src, dst=dst, cmd=0x4f, tns=tns, data=data)

    def get_data(self, file_type):
        if file_type in {FileType.ASCII, FileType.STATUS}:
            data = list(self._get_command_data())
            return data
        elif file_type == FileType.INTEGER:
            data = list(self._get_command_data())
            if len(data) % 2:
                raise ArithmeticError("get_data FileType.INTEGER but data contains odd number of elements.")
            return list(self.__pop_integer_data(data))
        elif file_type == FileType.BIT:
            data = list(self._get_command_data())
            return list(self.__pop_integer_data(data))
        elif file_type == FileType.FLOAT:
            data = list(self._get_command_data())
            if len(data) == 0:
                return []
            if len(data) % 4:
                raise ArithmeticError("get_data FileType.FLOAT but data does not contain multiple of 4 bytes for IEEE.")
            return list(self.__pop_float_data(data))
        else:  # pragma: nocover
            raise NotImplementedError("Only INTEGER, Float, BIT are implemented at the moment.")

    def __pop_integer_data(self, data):
        data = list(data)
        while data:
            yield (data.pop(0) & 0xff) + (data.pop(0) << 8)

    def __pop_float_data(self, data):
        data = list(data)
        while data:
            # print('Float Size',len(data), 'data', data[:4])
            parse = self._convert_bytes_to_float(data[:4])
            del data[:4]
            yield (parse)

    def _convert_bytes_to_float(self, data: bytearray):
        # list = []
        # list = data
        ieee754 = bytes(data)
        return struct.unpack('f', ieee754)[0]