# -*- encoding: utf-8 -*-

"""Transaction model for OAP"""
class Transaction(object):
    def __init__(self, date, description, amount, balance):
        self.date = date
        self.description = description
        self.amount = amount
        self.balance = balance