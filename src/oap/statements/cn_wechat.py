# -*- encoding: utf-8 -*-
import re, datetime, decimal, locale
import openpyxl
from oap.utils import moneyfmt
from .base import BaseStatementProvider, BaseStatement, BaseTransaction

class WechatStatement(BaseStatement):
    def __init__(self):
        super(WechatStatement, self).__init__()
    def set_apply_datetime(self, datetime_str):
        self.apply_dt = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    
    def set_query_dt_span(self, start_str, end_str):
        self.query_start_at = datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
        self.query_end_at = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        
class WechatTransaction(BaseTransaction):
    def __init__(self, rows):
        super(WechatTransaction, self).__init__()

        self.txn_dt = datetime.datetime.strptime(rows[0].strip(), "%Y-%m-%d %H:%M:%S")

        self.postscript = rows[10].strip()
        # Convert money strings to decimal

        self.amount = decimal.Decimal(locale.delocalize(rows[5].strip().replace(locale.localeconv()['currency_symbol'], '')))
        

    def __repr__(self):
        return f"WechatTransaction(txn_dt={self.txn_dt}, amount={self.amount}, balance={self.balance}, postscript={self.postscript})"
    
class ChinaWechatProvider(BaseStatementProvider):
    TITLE = "微信支付账单明细"
    ACCOUNT_NAME_RE = re.compile(r"^微信昵称：\[(?P<wechat_id>.+)\]$")
    TIMESPAN_RE = re.compile(r"^起始时间：\[(?P<start_at>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] 终止时间：\[(?P<end_at>\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2})\]$")
    APPLY_DT_RE = re.compile(r"^导出时间：\[(?P<apply_dt>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]$")
    def __init__(self):
        self._cur_statement = None

    def start(self, file):
        # TODO Implement WeChat statement parsing
        loc = locale.getlocale()
        locale.setlocale(locale.LC_ALL, "zh_CN.UTF-8")
        self._cur_statement = WechatStatement()
        xlsx_statement = openpyxl.open(file)
        active_sheet = xlsx_statement["Sheet1"]
        if not self.fill_statement_base(active_sheet):
            return False
        if not self.fill_transactions(active_sheet):
            return False

        locale.setlocale(locale.LC_ALL, loc)
        # Parsing logic goes here
        return self._cur_statement
    
    def fill_statement_base(self, active_sheet):
        
        if active_sheet["A1"].value != self.TITLE:
            return False
        # We just ignore wechat_id for now
        m = self.ACCOUNT_NAME_RE.match(active_sheet["A2"].value)
        if m is None:
            return False
        
        self._cur_statement.account_name = m.group("wechat_id").strip()
        m = self.TIMESPAN_RE.match(active_sheet["A3"].value)
        if m is None:
            return False
        self._cur_statement.set_query_dt_span(m.group("start_at"), m.group("end_at"))
        
        m = self.APPLY_DT_RE.match(active_sheet["A5"].value)
        if m is None:
            return False
        self._cur_statement.set_apply_datetime(m.group("apply_dt"))


        return True

    def fill_transactions(self, active_sheet):
        # Locate the header row
        found_header = False
        for row, row_cells in enumerate(active_sheet.iter_rows(values_only=True), start=1):
            if found_header:
                if row_cells[0] is None or row_cells[0].strip() == "":
                    continue
                transaction = WechatTransaction(row_cells)
                self._cur_statement.transactions.append(transaction)
            elif row_cells[0] == "交易时间":
                print("Found header at row", row)
                found_header = True
                continue

        return True