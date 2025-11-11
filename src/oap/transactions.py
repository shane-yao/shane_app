# -*- encoding: utf-8 -*-
import decimal

class SubTransaction(object):
    def __init__(self, account, description, amount):
        self.account = account
        self.description = description
        self.amount = amount
        self.commodity = "CNY"
        self.price = decimal.Decimal()

"""Transaction model for OAP"""
class Transaction(object):
    def __init__(self, date, description):
        self.date = date
        self.description = description
        self.meta = {}
        self.flags = set()
        self.sub_transactions = []

    def add_sub_txn(self, account, description, amount):
        new_sub_txn = SubTransaction(account, description, amount)
        self.sub_transactions.append(new_sub_txn)
        return new_sub_txn
    
    def export_beancount(self):
        lines = []
        lines.append(f"{self.date.strftime('%Y-%m-%d')} * \"{self.description}\"")
        for sub_txn in self.sub_transactions:
            amt_str = f"{sub_txn.amount:.2f}"
            lines.append(f"    {sub_txn.account}    {amt_str} {sub_txn.commodity}  ; {sub_txn.description}")
        return "\n".join(lines)
