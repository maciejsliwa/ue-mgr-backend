import os
from datetime import datetime, timedelta
from pymongo import MongoClient

from src.classes.StreamingHistory import StreamingHistory

MONGO_CONNECTION_STRING = os.environ.get('MONGO_CONNECTION_STRING', '')


class StreamingHistoryDbContext:
    def __init__(self):
        self.client = MongoClient(MONGO_CONNECTION_STRING)
        self.database = self.client.get_database('streaminghistory')
        self.collection = self.database['tracks']

    def save_streaming_history(self, sh: StreamingHistory):
        for day in sh.get_days():
            day_sh = sh.get_object_by_day(day)
            self.collection.insert_one(day_sh.dict())

    def get_data_time_range(self, username: str) -> (datetime, datetime):
        min_date = self.collection.find_one({"username": username}, sort=[("ts", 1)])
        max_date = self.collection.find_one({"username": username}, sort=[("ts", -1)])
        return datetime.fromtimestamp(min_date['ts'] / 1000), datetime.fromtimestamp(max_date['ts'] / 1000)

    def get_last_played_track(self, username: str) -> str:
        items = self.collection.find({"username": username}).sort("date", -1).limit(1)
        return items[0]['history_list'][-1]['master_metadata_track_name']

    def get_tracks_by_day(self, date: str, username: str):
        items = self.collection.find({
            "username": username,
            "date": date
        })
        return list(items)

    def get_daily_sentiments(self, username: str, date: datetime):
        first_day = date.replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        items = self.collection.find({"username": username, "date": {"$gte": first_day, "$lte": last_day}})
        daily_sentiments = {}

        for item in items:
            if item['date'] not in daily_sentiments:
                daily_sentiments[item['date']] = {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                }
            daily_sentiments[item['date']]['positive'] += item['sentimentAvg']['positive']
            daily_sentiments[item['date']]['neutral'] += item['sentimentAvg']['neutral']
            daily_sentiments[item['date']]['negative'] += item['sentimentAvg']['negative']

        result = []
        for item['date'], sentiments in daily_sentiments.items():
            result.append({
                "date": item['date'].isoformat(),
                "positive": sentiments['positive'],
                "neutral": sentiments['neutral'],
                "negative": sentiments['negative']
            })
        return result
