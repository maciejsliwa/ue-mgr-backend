from datetime import datetime
from src.classes.StreamingHistoryItem import StreamingHistoryItem


class StreamingHistory:
    def __init__(self, file: list, file_name: str):
        self.file_name = file_name
        self.username = file[0]['username']
        self.history_list = self._load_json(file)

    def _load_json(self, file: list) -> list:
        return [StreamingHistoryItem(item) for item in file]

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

    def get_last_track(self):
        sorted_list = sorted(self.history_list, key=lambda item: item.ts)
        last_track = sorted_list[-1]
        return last_track.master_metadata_track_name

    def get_months(self) -> list:
        dates = [item.ts for item in self.history_list]
        return sorted(set((date.year, date.month) for date in dates))

    def get_items_by_month(self, year: int, month: int) -> list:
        return [item.to_dict() for item in self.history_list if item.ts.year == year and item.ts.month == month]

    def get_date_range_for_month(self, year: int, month: int) -> (str, str):
        items = [item for item in self.history_list if item.ts.year == year and item.ts.month == month]
        if not items:
            return None, None

        min_date = min(item.ts for item in items)
        max_date = max(item.ts for item in items)

        return min_date.isoformat(), max_date.isoformat()
