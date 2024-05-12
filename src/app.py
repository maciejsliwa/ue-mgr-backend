import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

import requests
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from bs4 import BeautifulSoup
from fastapi import FastAPI, UploadFile, BackgroundTasks, Depends
from src.classes.DatabaseContext import DatabaseContext
from fastapi.middleware.cors import CORSMiddleware
from fastapi.param_functions import File
import spotipy
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.classes.StreamingHistory import StreamingHistory
from lyricsgenius import Genius
import asyncio
from concurrent.futures import ThreadPoolExecutor
from Levenshtein import distance

app = FastAPI()

GENIUS_TOKEN = os.environ.get('GENIUS_TOKEN', '')

origins = [
    "http://sentimental-spotify.azurewebsites.net/",
    "sentimental-spotify.azurewebsites.net/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def authenticate_azure_cognitive_client():
    ta_credential = AzureKeyCredential(os.environ.get('LANG_KEY', ''))
    text_analytics_client = TextAnalyticsClient(
        endpoint=os.environ.get('LANG_HOST', ''),
        credential=ta_credential)
    return text_analytics_client


cog_srv = authenticate_azure_cognitive_client()
db = DatabaseContext()


@app.post("/uploadFiles")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    contents = await file.read()
    try:
        json_contents = json.loads(contents)
        sh = StreamingHistory(json_contents, file.filename)
        background_tasks.add_task(db.save_streaming_history(sh))
        return {"status_ok": "FIle was saved"}
    except json.JSONDecodeError:
        return {"error": "Provided file is not valid JSON"}


@app.get("/getRange")
async def get_range(token: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    sp = spotipy.Spotify(auth=token.credentials)
    user = sp.current_user()
    username = user['id']
    min, max = db.get_data_time_range(username)
    return {"min": min, "max": max}


@app.get("/getLast")
async def get_recently_played(token: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    sp = spotipy.Spotify(auth=token.credentials)
    user = sp.current_user()
    username = user['id']
    return {"recently_played": db.get_last_played_track(username)}


@app.post("/getPlaylistByDay/")
async def get_playlist_by_day():
    page = requests.get('https://genius.com/Sanah-irenka-lyrics')
    html = BeautifulSoup(page.text, "html.parser")
    [h.extract() for h in html('script')]
    lyrics = [html.find("div", {"data-lyrics-container": "true"}).get_text(' ')]
    result = cog_srv.analyze_sentiment(lyrics, show_opinion_mining=False)
    return result


@app.post("/getSentimentByMonth/")
async def get_sentiment_by_month(date: str, token: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    sp = spotipy.Spotify(auth=token.credentials)
    user = sp.current_user()
    username = user['id']
    tracks = db.get_tracks_by_month(date, username)
    genius = Genius(access_token=GENIUS_TOKEN, timeout=30)
    sys.stdout = open(os.devnull, 'w')

    def fetch_track_info(track):
        try:
            track_info = None
            title = re.split(r'[^a-zA-Z0-9 ,]', track['master_metadata_track_name'])[0]
            author = re.split(r'[^a-zA-Z0-9 ,]', track['master_metadata_album_artist_name'])[0]
            track_info = genius.search_song(title=title, artist=author, get_full_info=False)
            if (track_info and track_info.lyrics
                    and (author in track_info.artist or distance(author, track_info.artist) <= 5)):
                res_sentiment = cog_srv.analyze_sentiment([track_info.lyrics], show_opinion_mining=False)
                if res_sentiment and res_sentiment[0] and 'sentiment' in res_sentiment[0]:
                    track['sentiment'] = res_sentiment[0]['sentiment']
        except TimeoutError:
            track['error'] = 'timeout'

    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        await asyncio.gather(*(loop.run_in_executor(executor, fetch_track_info, track) for track in tracks))
    sys.stdout = sys.__stdout__
    sentiments_by_date = {}
    for track in tracks:
        if 'sentiment' in track:
            date = datetime.strptime(track['ts'], '%Y-%m-%dT%H:%M:%S%z').date()
            sentiment = track['sentiment']
            if date not in sentiments_by_date:
                sentiments_by_date[date] = []
            sentiments_by_date[date].append(sentiment)
    for date, sentiments in sentiments_by_date.items():
        counter = Counter(sentiments)
        most_common_sentiment = counter.most_common(1)[0][0]
        sentiments_by_date[date] = most_common_sentiment
    return sentiments_by_date
