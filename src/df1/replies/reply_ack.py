# -*- coding: utf-8 -*-

from df1.replies.base_simple_reply import BaseSimpleReply
from df1.models.tx_symbol import TxSymbol


class ReplyAck(BaseSimpleReply):
    def __init__(self):
        super(ReplyAck, self).__init__(TxSymbol.ACK)
