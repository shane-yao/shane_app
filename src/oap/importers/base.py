# -*- encoding -*-: utf-8
"""General importer for OAP """

class BaseImporter(object):
    def __init__(self):
        pass
    def start(self, file):
        raise NotImplementedError("Subclasses must implement start method")
    