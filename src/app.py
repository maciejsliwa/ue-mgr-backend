import json
import os
import re
import time
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
from Levenshtein import distance

app = FastAPI()

GENIUS_TOKEN = os.environ.get('GENIUS_TOKEN', '')

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


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/uploadFiles")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    contents = await file.read()
    try:
        json_contents = json.loads(contents)
        sh = StreamingHistory.parse_obj({
            'file_name': file.filename,
            'username': json_contents[0]['username'],
            'history_list': json_contents
        })
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


@app.get("/getSentiment/")
async def get_sentiment(artist: str, title: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
        'Authorization': 'Bearer ' + GENIUS_TOKEN
    }
    search_url = f"https://api.genius.com/search?q={artist}%20{title}"
    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        return {"error": "Failed to search for the song"}
    response_json = response.json()
    for hit in response_json["response"]["hits"]:
        find_artist = hit["result"]["primary_artist"]["name"].lower()
        if artist.lower() in find_artist or distance(find_artist, artist.lower()) <= 3:
            song_url = hit["result"]["url"]
            break
    else:
        return {"error": "Song not found"}
    headers['Authorization'] = ''
    page = requests.get(song_url, headers=headers)
    html = BeautifulSoup(page.text, "html.parser")
    [h.extract() for h in html('script')]
    # lyrics = [html.find("div", {"data-lyrics-container": "true"}).get_text(' ')]
    # result = cog_srv.analyze_sentiment(lyrics, show_opinion_mining=False)
    return {"html": str(html.body)}


@app.post("/getSentimentByMonth/")
async def get_sentiment_by_month(date: str, token: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    sp = spotipy.Spotify(auth=token.credentials)
    user = sp.current_user()
    username = user['id']
    tracks = db.get_tracks_by_month(date, username)
    genius = Genius(access_token=GENIUS_TOKEN, timeout=50)
    for track in tracks:
        try:
            if track['master_metadata_track_name'] and track['master_metadata_album_artist_name']:
                track_info = None
                title = re.split(r'[^a-zA-Z0-9 ,]', track['master_metadata_track_name'])[0]
                author = re.split(r'[^a-zA-Z0-9 ,]', track['master_metadata_album_artist_name'])[0]
                track_info = genius.search_song(title=title, artist=author, get_full_info=False)
                if (track_info and track_info.lyrics
                        and (author in track_info.artist or distance(author, track_info.artist) <= 5)):
                    res_sentiment = cog_srv.analyze_sentiment([track_info.lyrics], show_opinion_mining=False)
                    if res_sentiment and res_sentiment[0] and 'sentiment' in res_sentiment[0]:
                        track['sentiment'] = res_sentiment[0]['sentiment']
        except requests.exceptions.HTTPError as e:
            if e and e.response and e.response.status_code and e.response.status_code == 403:
                time.sleep(1)
            else:
                track['error'] = e.__repr__()
        except TimeoutError:
            track['error'] = 'timeout'
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
    return sentiments_by_date if len(sentiments_by_date.keys()) > 0 else tracks
