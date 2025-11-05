#-*- encoding: utf-8 -*-
# from application import Application
from oap.importers.cn_bnk_grc import CNBankGRCImporter

def main():
    # app = Application()
    # app.run()
    print(">>>>>>>>", CNBankGRCImporter().start(r"e:\download\20251104172013\20251104172013.pdf").transactions)


if __name__ == "__main__":
    main()