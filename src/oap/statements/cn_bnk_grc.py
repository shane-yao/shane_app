
import re, datetime, locale, decimal
import pdfplumber

from .base import BaseStatementProvider, BaseStatement, BaseTransaction

class GRCStatement(BaseStatement):
    def __init__(self):
        super().__init__()

    def set_apply_datetime(self, datetime_str):
        self.apply_dt = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    
    def set_query_dt_span(self, timespan_str):
        self.query_start_at = datetime.datetime.strptime(timespan_str[0:8], "%Y%m%d")
        self.query_end_at = datetime.datetime.strptime(timespan_str[9:16], "%Y%m%d")

class GRCTransaction(BaseTransaction):
    HEADER = ["序号", "交易日期", "交易金额", "账户余额", "对方账号", "对方账户名", "对方开户行", "摘要", "附言"]
    @staticmethod
    def NORMALIZED_HEADER(header):
        for col_idx in range(len(header)):
            header[col_idx] = header[col_idx].replace('\n', '').strip()
        assert(header == GRCTransaction.HEADER)
               
    def __init__(self, row):
        assert(len(row) == len(self.HEADER))
        super().__init__()
        self.seq = int(row[0].strip())
        self.txn_dt = datetime.datetime.strptime(row[1].strip(), "%Y%m%d")
        self.amount = decimal.Decimal(locale.delocalize(row[2].strip()))
        self.balance = decimal.Decimal(locale.delocalize(row[3].strip()))
        self.other_account_id = row[4].strip()
        self.other_account_name = row[5].strip()
        self.other_bank = row[6].strip()
        self.summary = row[7].strip()
        self.postscript = row[8].strip()

    def __repr__(self):
        return f"GRCTransaction(seq={self.seq}, txn_dt={self.txn_dt}, amount={self.amount}, balance={self.balance}, other_account_id={self.other_account_id}, other_account_name={self.other_account_name}, other_bank={self.other_bank}, summary={self.summary}, postscript={self.postscript})"
    
class ChinaBankGRCProvider(BaseStatementProvider):
    TITLE = "广州农商银行"
    SEC_TITLE = "账户交易流水对账单"
    NAME = "ChinaBankGRCProvider"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cur_statement = None

    def start(self, file):
        loc = locale.getlocale()
        locale.setlocale(locale.LC_ALL, "zh_CN.UTF-8")
        # TODO Check cur statement
        self._cur_statement = GRCStatement()
        self._cur_statement.provider = self.key
        with pdfplumber.open(file) as pdf:
            self.fill_statement_base(pdf)
            self.fill_transactions(pdf)
        print(self._cur_statement)
        # Resume locale
        locale.setlocale(locale.LC_ALL, loc)
        return self._cur_statement
    
    def fill_statement_base(self, pdf):
        assert(self._cur_statement)
        index_page = pdf.pages[0]
        text_lines = index_page.extract_text().split('\n')
        if text_lines[0].strip() != self.TITLE:
            return False
        self._cur_statement.title = self.TITLE
        sec_title, signed = text_lines[1].strip().split(" ")
        if sec_title.strip() != self.SEC_TITLE:
            return False
        self._cur_statement.signed = signed.strip()
        match = re.fullmatch("([^:^ ]*): ([^:^]*) ([^:^ ]*): (.*)", text_lines[2].strip())
        # Should match the pattern like "账户名称: 张三 账户时间段: 20230101-20230131"
        if match and match.lastindex == 4:
            if match.group(1).strip() == "账户名称":
                self._cur_statement.account_name = match.group(2).strip()
            if match.group(3).strip() == "查询起止日期":
                self._cur_statement.set_query_dt_span(match.group(4).strip())

        match = re.fullmatch("([^:^ ]*): ([^:^]*) ([^:^ ]*): (.*)", text_lines[3].strip())
        # Should match the pattern like "账户名称: 张三 账户时间段: 20230101-20230131"
        if match and match.lastindex == 4:
            if match.group(1).strip() == "账户账号":
                self._cur_statement.account_id = match.group(2).strip()
            if match.group(3).strip() == "账单申请时间":
                self._cur_statement.set_apply_datetime(match.group(4).strip())
        
    def fill_transactions(self, pdf):
        # peek header
        seq = 0
        header = None
        for page in pdf.pages:
            tbl = page.extract_table()
            for row in tbl:
                if row[0] == '':
                    continue
                if seq == 0:
                    header = pdf.pages[0].extract_table()[0]
                    GRCTransaction.NORMALIZED_HEADER(header)
                else:
                    transaction = GRCTransaction(row)
                    self._cur_statement.transactions.append(transaction)
                    assert(seq == transaction.seq)
                seq += 1

        #     # 这里根据具体的 PDF 格式进行解析
        #     # 假设每行代表一笔交易，字段用空格分隔
        #     for line in text.split('\n'):
        #         fields = line.split()
        #         if len(fields) >= 4:
        #             date = fields[0]
        #             description = ' '.join(fields[1:-2])
        #             amount = fields[-2]
        #             balance = fields[-1]
        #             transaction = {
        #                 'date': date,
        #                 'description': description,
        #                 'amount': amount,
        #                 'balance': balance
        #             }
        #             transactions.append(transaction)