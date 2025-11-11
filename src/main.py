#-*- encoding: utf-8 -*-
# from application import Application
from oap.statements.cn_bnk_grc import ChinaBankGRCProvider
from oap.statements.cn_wechat import ChinaWechatProvider
from oap.export_mgr import ExportManager

def main():
    # app = Application()
    # app.run()
    # print(">>>>>>>>", ChinaBankGRCImporter().start(r"e:\download\20251104172013\20251104172013.pdf").transactions)
    ipt_mgr = ExportManager("e:/projects/shane_app/oap_config.yaml")
    ipt_mgr.load_config()
    ipt_mgr.load_all_files()
    ipt_mgr.export_all()


if __name__ == "__main__":
    main()