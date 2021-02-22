# -*- coding: utf-8 -*-

from df1.commands.base_command import BaseCommand
from df1.file_type import FileType

class Command0FA2(BaseCommand):
    """
    protected typed logical read with three address fields
    Official doc 7-17
    """
    def init_with_params(self, bytes_to_read, table, file_type, start, start_sub=0x0, **kwargs):
        if start > 0xfe or start_sub > 0xfe or table > 0xfe:  # pragma: nocover
            raise NotImplementedError("Table, start and start sub higher than 0xfe not supported yet.")
        data = [bytes_to_read, table, file_type.value, start, start_sub]
        super(Command0FA2, self).init_with_params(cmd=0x0f, fnc=0xa2, command_data=data, **kwargs)


class Command0FAA(BaseCommand):
    """
    protected typed logical write with three address fields
    Official doc 7-18
    """
    def init_with_params(self, table, file_type, start, data_to_write, start_sub=0x0, **kwargs):
        if file_type in {FileType.INTEGER,FileType.OUT_LOGIC, FileType.BIT, FileType.CONTROL}:
            bytes_to_write = [b for i in data_to_write for b in self._swap_endian(i)]
        elif file_type in {file_type.FLOAT}:
            bytes_to_write = bytes(data_to_write)
        else:  # pragma: nocover
            raise NotImplementedError()
        if start > 0xfe or start_sub > 0xfe or table > 0xfe:  # pragma: nocover
            raise NotImplementedError("Table, start, and start sub higher than 0xfe not supported yet.")
        data = [len(bytes_to_write), table, file_type.value, start, start_sub]
        data.extend(bytes_to_write)
        super(Command0FAA, self).init_with_params(cmd=0x0f, fnc=0xaa, command_data=data, **kwargs)


class Command0FAB(BaseCommand):
    """
    Protected Typed Logical Write with Mask
    Unofficial. See:
    http://www.iatips.com/pccc_tips.html#slc5_cmds
    http://forums.mrplc.com/index.php?/topic/677-writing-my-own-df1-driver/
    http://iatips.com/docs/DF1%20Protocol%2017706516%20Suppliment.pdf page 12
    """
    def init_with_params(self, table, file_type, start, bit_mask, data_to_write, start_sub=0x0, **kwargs):
        if file_type in [FileType.INTEGER, FileType.BIT, FileType.FLOAT]:
            bytes_to_write = [b for i in data_to_write for b in self._swap_endian(i)]
        else:  # pragma: nocover
            raise NotImplementedError()
        if start > 0xfe or start_sub > 0xfe or table > 0xfe:  # pragma: nocover
            raise NotImplementedError("Table, start, and start sub higher than 0xfe not supported yet.")
        data = [len(bytes_to_write), table, file_type.value, start, start_sub]
        data.extend(self._swap_endian(bit_mask))
        data.extend(bytes_to_write)
        super(Command0FAB, self).init_with_params(cmd=0x0f, fnc=0xab, command_data=data, **kwargs)


class Command0FABSingleBit(Command0FAB):
    def init_with_params(self, table, file_type, start, bit_position, bit_value, **kwargs):
        bit_mask = pow(2, bit_position)
        data_to_write = [bit_value * bit_mask]
        super(Command0FABSingleBit, self).init_with_params(table, file_type, start, bit_mask, data_to_write, **kwargs)


class Command0F04(BaseCommand):
    """
    protected typed logical read with three address fields
    Official doc 7-17
    """
    def init_with_params(self, bytes_to_read, table, file_type, start, start_sub=0x0, **kwargs):
        if start > 0xfe or start_sub > 0xfe or table > 0xfe:  # pragma: nocover
            raise NotImplementedError("Table, start and start sub higher than 0xfe not supported yet.")
        data = [bytes_to_read, table, file_type.value, start, start_sub]
        super(Command0F04, self).init_with_params(cmd=0x0f, fnc=0x04, command_data=data, **kwargs)

class Command0600(BaseCommand): # Echo (TODO)
    """
    protected typed logical read with three address fields
    Official doc 7-17
    """
    def init_with_params(self, table, data_to_write, **kwargs):
        data = data_to_write
        super(Command0600, self).init_with_params(cmd=0x06, fnc=0x00, command_data=data, **kwargs)


class Command0603(BaseCommand): # Get Diagnostic Status (TODO)
    """
    protected typed logical read with three address fields
    Official doc 7-17
    """
    def init_with_params(self, bytes_to_read, table, file_type, start, start_sub=0x0, **kwargs):
        if start > 0xfe or start_sub > 0xfe or table > 0xfe:  # pragma: nocover
            raise NotImplementedError("Table, start and start sub higher than 0xfe not supported yet.")
        data = [bytes_to_read, table, file_type.value, start, start_sub]
        super(Command0603, self).init_with_params(cmd=0x06, fnc=0x03, command_data=data, **kwargs)
