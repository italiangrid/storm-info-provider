import logging
import json

class Report:

    def __init__(self, **data):
      # required:
      if data.get("storage_service"):
        self.storageservice = data.get("storage_service")

    def get_storage_service(self):
      return self.storageservice

    def to_json(self):
      return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
