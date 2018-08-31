# -*- coding: utf-8 -*-

from .base_simple_reply import BaseSimpleReply
from .tx_symbol import TxSymbol


class ReplyNak(BaseSimpleReply):
    def __init__(self):
        super(ReplyNak, self).__init__(TxSymbol.NAK)
