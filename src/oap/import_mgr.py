from .statements.base import BaseStatementProvider
from .statements.cn_wechat import ChinaWechatProvider
from .statements.cn_bnk_grc import ChinaBankGRCProvider
from .transactions import Transaction

class ImportManager(object):
    def __init__(self):
        self.file_to_import = []
        self.importers = []
        self.statements_provider = {
            "cn_wechat": ChinaWechatProvider(),
            "cn_bnk_grc": ChinaBankGRCProvider(),
        }

    def load_all_files(self):
        for provider_key, file_path in self.file_to_import:
            provider = self.statements_provider.get(provider_key)
            if provider is None:
                print(f"Provider {provider_key} not found")
                continue
            statement = provider.start(file_path)
            if statement is None:
                print(f"Failed to import file {file_path} with provider {provider_key}")
                continue
            print(f"Imported statement: {statement}")
        

    def add_file_with_provider(self, provider, file_path):
        self.file_to_import = (provider, file_path)


    def register_importer(self, importer):
        self.importers.append(importer)