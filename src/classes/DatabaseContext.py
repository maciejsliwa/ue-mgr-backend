import os
from datetime import datetime
from pymongo import MongoClient
from src.classes import StreamingHistory


MONGO_CONNECTION_STRING = os.environ.get('MONGO_CONNECTION_STRING', '')


class DatabaseContext:
    def __init__(self):
        self.client = MongoClient(MONGO_CONNECTION_STRING)
        self.database = self.client.get_database('streaminghistory')
        self.collection = self.database['tracks']

    def save_streaming_history(self, sh: StreamingHistory):
        for month in sh.get_months():
            new_id = f"{sh.file_name}_{month[0]}_{month[1]}"
            min_date, max_date = sh.get_date_range_for_month(*month)
            body = dict(id=new_id, username=sh.username, min_date=min_date, max_date=max_date,
                        tracks=sh.get_items_by_month(*month))
            self.collection.insert_one(body)

    def get_data_time_range(self, username: str) -> (datetime, datetime):
        min = self.collection.find_one({"username": username}, sort=[("min_date", 1)])
        max = self.collection.find_one({"username": username}, sort=[("max_date", -1)])
        return datetime.fromisoformat(min['min_date']), datetime.fromisoformat(max['max_date'])

    def get_last_played_track(self, username: str) -> str:
        items = self.collection.find({"username": username}).sort("max_date", -1).limit(1)
        return items[0]['tracks'][-1]['master_metadata_track_name']

    def get_tracks_by_month(self, date: str, username: str):
        year, month = date.split('-')[:2]
        next_month = str(int(month) % 12 + 1).zfill(2)
        next_year = str(int(year) + 1) if next_month == '01' else year
        items = self.collection.find({
            "username": username,
            "min_date": {"$gte": f"{year}-{month}-01T00:00:00Z"},
            "max_date": {"$lt": f"{next_year}-{next_month}-01T00:00:00Z"}
        })
        return list(items)
