from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Tuple
from src.classes.StreamingHistoryItem import StreamingHistoryItem


class StreamingHistory(BaseModel):
    file_name: str
    username: str = Field(alias='username')
    history_list: List[StreamingHistoryItem]

    @property
    def get_data_time_range(self) -> Tuple[datetime, datetime]:
        date_min = min(item.ts for item in self.history_list)
        date_max = max(item.ts for item in self.history_list)
        return date_min, date_max

    @property
    def get_last_track(self):
        sorted_list = sorted(self.history_list, key=lambda item: item.ts)
        last_track = sorted_list[-1]
        return last_track.master_metadata_track_name

    @property
    def get_months(self) -> List[Tuple[int, int]]:
        dates = [item.ts for item in self.history_list]
        return sorted(set((date.year, date.month) for date in dates))

    def get_items_by_month(self, year: int, month: int) -> List[dict]:
        return [item.dict() for item in self.history_list if item.ts.year == year and item.ts.month == month]

    def get_date_range_for_month(self, year: int, month: int) -> Tuple[str, str]:
        items = [item for item in self.history_list if item.ts.year == year and item.ts.month == month]
        if not items:
            return None, None

        min_date = min(item.ts for item in items)
        max_date = max(item.ts for item in items)

        return min_date.isoformat(), max_date.isoformat()

