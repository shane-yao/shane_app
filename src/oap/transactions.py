# -*- encoding: utf-8 -*-
import decimal

class SubTransaction(object):
    def __init__(self, description, amount):
        self.account = ""
        self.description = description
        self.amount = amount
        self.commodity = ""
        self.price = decimal.Decimal()

"""Transaction model for OAP"""
class Transaction(object):
    def __init__(self, date, description, amount, balance):
        self.date = date
        self.description = description
        self.meta = {}
        self.flags = set()
        self.sub_transactions = []
