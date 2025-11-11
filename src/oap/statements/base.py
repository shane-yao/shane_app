# -*- encoding -*-: utf-8
"""General importer for OAP """

from decimal import Decimal
from oap.transactions import Transaction

class BaseStatement(object):
    def __init__(self):
        self.provider = None
        self.signed = ""
        self.title = ""
        self.account_name = ""
        self.account_id = ""
        self.apply_dt = None
        self.transactions = []
        self.query_start_at = None
        self.query_end_at = None

    def __repr__(self):
        return f"Statement(signed={self.signed}, title={self.title}, account_name={self.account_name}, account_id={self.account_id}, txn_len={len(self.transactions)}, apply_dt={self.apply_dt}), query_span=[{self.query_start_at} {self.query_end_at}]"
    
class BaseStatementProvider(object):
    NAME = "BaseStatementProvider"
    def __init__(self, key, class_name, params):
        assert(self.NAME == class_name)
        self.key = key
        self.params = params
        
    def start(self, file):
        raise NotImplementedError("Subclasses must implement start method")
    
    def get_param(self, name, default=None):
        return self.params.get(name, default)
    
class BaseTransaction(object):
    def __init__(self):
        self.txn_dt = None
        self.amount = Decimal()
        self.postscript = ""
        self.payer_account = None
        self.payee_account = None

    def to_beancount_txn(self):
        new_txn = Transaction(self.txn_dt, self.postscript)
        new_txn.add_sub_txn(self.payer_account, "", self.amount)
        new_txn.add_sub_txn(self.payee_account, "", -self.amount)
        return new_txn

    def __repr__(self):
        return f"BaseTransaction(txn_dt={self.txn_dt}, payment_account={self.payer_account}, amount={self.amount}, postscript={self.postscript})"