from info_provider.model.storage_service import *

class Report:

    def __init__(self, storage_service):
        self.storage_service = storage_service
        return

    def save_to_file(self, file_path):
        file = open(file_path, 'w')
        file.write(self.storage_service.to_json())
        file.close()