import os
import time
import pymongo
from pymongo import MongoClient, errors
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from statistics import mean

from src.classes.StreamingHistoryItem import StreamingHistoryItem
from src.classes.SentimentScore import SentimentScore


MONGO_CONNECTION_STRING = os.environ.get('MONGO_CONNECTION_STRING', '')


def authenticate_azure_cognitive_client():
    ta_credential = AzureKeyCredential(os.environ.get('LANG_KEY', ''))
    text_analytics_client = TextAnalyticsClient(
        endpoint=os.environ.get('LANG_HOST', ''),
        credential=ta_credential)
    return text_analytics_client


class SentimentAnalyseContext:
    def __init__(self):
        self.client = MongoClient(MONGO_CONNECTION_STRING)
        self.database = self.client.get_database('lirycs')
        self.collection = self.database['genius']
        self.azure_client = authenticate_azure_cognitive_client()

    def update_sentiment(self, item: StreamingHistoryItem):
        query = {
            'artist': {"$regex": f".*{item.master_metadata_album_artist_name}.*", "$options": "i"},
            'title': {"$regex": f".*{item.master_metadata_track_name}.*", "$options": "i"}
        }
        try:
            document = self.collection.find_one(query)
            if document is not None:
                lyrics = document['lyrics'].replace('\\n', '\n').replace('\\', ' ')
                chunks = []
                while lyrics:
                    if len(lyrics) > 5120:
                        split_index = lyrics.rfind('\n', 0, 5120)
                        chunk, lyrics = lyrics[:split_index], lyrics[split_index:]
                    else:
                        chunk, lyrics = lyrics, ''
                    chunks.append(chunk)
                chunks_limit = min(len(chunks), 10)
                response = self.azure_client.analyze_sentiment(chunks[:chunks_limit], language=document['lang'])

                if response:
                    positives = [res.positive for res in response]
                    neutrals = [res.neutral for res in response]
                    negatives = [res.negative for res in response]
                    item.sentiment = SentimentScore(positive=mean(positives),
                                                    neutral=mean(neutrals),
                                                    negative=mean(negatives))
        except pymongo.errors.OperationFailure as e:
            if e.code == 16500:
                retry_after_ms = e.details.get('RetryAfterMs', 0)
                time.sleep(retry_after_ms / 1000)
                self.update_sentiment(item)
        except AttributeError as e:
            print("Limit document size to: 5120 text elements.")
        except Exception as e:
            print(e)
