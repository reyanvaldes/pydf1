# -*- coding: utf-8 -*-

from df1.replies.base_simple_reply import BaseSimpleReply
from df1.models.tx_symbol import TxSymbol


class ReplyNak(BaseSimpleReply):
    def __init__(self):
        super(ReplyNak, self).__init__(TxSymbol.NAK)
