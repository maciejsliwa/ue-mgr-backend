from pydantic import BaseModel


class SentimentScore(BaseModel):
    positive: float = 0.0
    neutral: float = 0.0
    negative: float = 0.0
