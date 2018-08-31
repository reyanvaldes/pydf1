# -*- coding: utf-8 -*-

from .base_simple_reply import BaseSimpleReply
from .tx_symbol import TxSymbol


class ReplyEnq(BaseSimpleReply):
    def __init__(self):
        super(ReplyEnq, self).__init__(TxSymbol.ENQ)
