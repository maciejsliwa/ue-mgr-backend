import json
import os
from datetime import datetime
from src.classes.StreamingHistoryItem import StreamingHistoryItem


class StreamingHistory:
    def __init__(self, file, file_type):
        self.file = file
        self.file_type = file_type
        self.history_list = self._load_json(file, file_type)

    # def _load_data(self):
    #     data = []
    #     for filename in os.listdir(self.files_path):
    #         if filename.endswith('.json'):
    #             with open(os.path.join(self.files_path, filename), 'r', encoding='utf-8') as file:
    #                 data.extend(json.load(file))
    #     return [StreamingHistoryItem(item) for item in data]

    def _load_json(self, file, file_type=None):
        if file_type == 'JSON':
            return [StreamingHistoryItem(item) for item in file]
        else:
            return []

    def get_item_by_timestamp(self, timestamp):
        for item in self.history_list:
            if item.offline_timestamp == timestamp:
                return item
        return None

    def get_all_items(self):
        return self.history_list

    def get_data_time_range(self) -> (datetime, datetime):
        date_min = min(item.ts for item in self.history_list)
        date_max = max(item.ts for item in self.history_list)
        return date_min, date_max
