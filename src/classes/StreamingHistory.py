from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Tuple
from statistics import mean

from src.classes.SentimentAnalyseContext import SentimentAnalyseContext
from src.classes.StreamingHistoryItem import StreamingHistoryItem
from src.classes.SentimentScore import SentimentScore

sa = SentimentAnalyseContext()


class StreamingHistory(BaseModel):
    file_name: str
    username: str
    date: datetime = Field(default_factory=datetime.now)
    history_list: List[StreamingHistoryItem]
    sentimentAvg: SentimentScore = Field(default_factory=SentimentScore)

    def get_data_time_range(self) -> Tuple[datetime, datetime]:
        date_min = min(item.ts for item in self.history_list)
        date_max = max(item.ts for item in self.history_list)
        return date_min, date_max

    def get_last_track(self) -> str:
        sorted_list = sorted(self.history_list, key=lambda item: item.ts)
        last_track = sorted_list[-1]
        return last_track.master_metadata_track_name

    def get_days(self) -> List[datetime]:
        dates = [item.ts.date() for item in self.history_list]
        return sorted(set(dates))

    def update_average_sentiment(self):
        positives = [item.sentiment.positive for item in self.history_list if
                     item.sentiment and sum(item.sentiment.dict().values()) > 0]
        neutrals = [item.sentiment.neutral for item in self.history_list if
                    item.sentiment and sum(item.sentiment.dict().values()) > 0]
        negatives = [item.sentiment.negative for item in self.history_list if
                     item.sentiment and sum(item.sentiment.dict().values()) > 0]

        if positives and neutrals and negatives:
            average_positive = mean(positives)
            average_neutral = mean(neutrals)
            average_negative = mean(negatives)

            self.sentimentAvg = SentimentScore(
                positive=average_positive,
                neutral=average_neutral,
                negative=average_negative
            )

    def get_object_by_day(self, date: datetime.date) -> 'StreamingHistory':
        filtered_history_list = [item for item in self.history_list if item.ts.date() == date]
        for item in filtered_history_list:
            sa.update_sentiment(item)
        day_sh = StreamingHistory(file_name=self.file_name,
                                  username=self.username,
                                  date=date,
                                  history_list=filtered_history_list)
        day_sh.update_average_sentiment()
        return day_sh
