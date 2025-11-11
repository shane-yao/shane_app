import yaml, importlib
from .transactions import Transaction

class ExportManager(object):
    def __init__(self, config_path=None):
        # Load config
        self.config_path = config_path
        self.config = None
        self.statements = []
        self.statement_list_by_key = {}
        self.provider_cls = {}
    
    def load_config(self):
        self.config = yaml.safe_load(open(self.config_path, encoding="utf-8")) if self.config_path else {}
        self.regist_all_providers()

    def _regist_provider(self, key, config):
        cls_path = config.pop("cls", None)
        if cls_path is None:
            return
        module_name, class_name = cls_path.rsplit('.', 1)
        module = importlib.import_module(module_name)
        provider_cls = getattr(module, class_name)
        config["class_name"] = class_name
        self.provider_cls[key] = (provider_cls, config)
        self.statement_list_by_key.setdefault(key, [])

    def _new_importer_provider(self, key):
        print(">>>>>>>>>>>>", key)
        provider_cls, cfg = self.provider_cls.get(key, None)
        if provider_cls is None:
            return
        
        new_importer = provider_cls(key, **cfg)
        return new_importer
    def regist_all_providers(self):
        importers = self.config.get("importers", {})
        for key, config in importers.items():
            self._regist_provider(key, config)

    def load_all_files(self):
        file_to_import = self.config.get("files", {})
        for file_entry in file_to_import:
            print(f"Load file:{file_entry}")
            provider_key = file_entry["key"]
            file_path = file_entry["file_path"]
            provider = self._new_importer_provider(provider_key)
            
            statement = provider.start(file_path)
            if statement is None:
                print(f"Failed to import file {file_path} with provider {provider_key}")
                continue
            print(f"Imported statement: {statement}")
            self._add_statement(statement)

    def _add_statement(self, statement):
        self.statements.append(statement)
        self.statement_list_by_key[statement.provider].append(statement)

    def add_file_with_provider(self, provider, file_path):
        self.file_to_import.append((provider, file_path))

    def export_all(self):
        for provider_key, statements in self.statement_list_by_key.items():
            for statement in statements:
                print(f";; Exporting statement for account: {statement.account_name}")
                for txn in statement.transactions:
                    beancount_txn = txn.to_beancount_txn()
                    print(beancount_txn.export_beancount())