from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from src.classes.SentimentScore import SentimentScore


class StreamingHistoryItem(BaseModel):
    ts: datetime = Field(default_factory=datetime.now)
    ms_played: Optional[int] = 0
    master_metadata_track_name: Optional[str] = ''
    master_metadata_album_artist_name: Optional[str] = ''
    master_metadata_album_album_name: Optional[str] = ''
    spotify_track_uri: Optional[str] = ''
    reason_start: Optional[str] = ''
    reason_end: Optional[str] = ''
    sentiment: SentimentScore = Field(default_factory=SentimentScore)
