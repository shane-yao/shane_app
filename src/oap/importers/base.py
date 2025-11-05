# -*- encoding -*-: utf-8
"""General importer for OAP """

class BaseStatement(object):
    def __init__(self):
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
    
class BaseImporter(object):
    def __init__(self):
        pass
    def start(self, file):
        raise NotImplementedError("Subclasses must implement start method")
    
class BaseTransaction(object):
    def __init__(self):
        self.txn_dt = None
        self.amount = 0.0
        self.postscript = ""

    def __repr__(self):
        return f"BaseTransaction(txn_dt={self.txn_dt}, amount={self.amount}, postscript={self.postscript})"