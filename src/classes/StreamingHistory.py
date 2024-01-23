import json
from datetime import datetime
from src.classes.StreamingHistoryItem import StreamingHistoryItem


class StreamingHistory:
    def __init__(self, file_path):
        self.file_path = file_path
        self.history_list = self._load_data()

    def _load_data(self):
        with open(self.file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return [StreamingHistoryItem(item) for item in data]

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

