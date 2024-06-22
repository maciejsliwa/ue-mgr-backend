import json
import os
import re
import zipfile
from datetime import datetime
from io import BytesIO
from fastapi import FastAPI, UploadFile, Depends, HTTPException
from src.classes.StreamingHistoryDbContext import StreamingHistoryDbContext
from fastapi.middleware.cors import CORSMiddleware
from fastapi.param_functions import File
import spotipy
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.classes.StreamingHistory import StreamingHistory

app = FastAPI()

GENIUS_TOKEN = os.environ.get('GENIUS_TOKEN', '')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = StreamingHistoryDbContext()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/uploadFiles")
async def upload_file(file: UploadFile = File(...)):
    if file.filename.endswith('.zip'):
        with zipfile.ZipFile(BytesIO(await file.read())) as zfile:
            for filename in zfile.namelist():
                if re.search(r'Streaming_History_Audio_\d{4}-\d{4}_\d.JSON', filename, re.IGNORECASE):
                    with zfile.open(filename) as f:
                        contents = f.read()
                        json_contents = json.loads(contents)
                        sh = StreamingHistory.parse_obj({
                            'file_name': filename,
                            'username': json_contents[0]['username'],
                            'history_list': json_contents
                        })
                        db.save_streaming_history(sh)
    else:
        raise HTTPException(status_code=400, detail="File is not a zip file")
    return {"status": "success"}


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


@app.get("/getSentimentByMonth")
async def get_sentiment(month: datetime):
    return db.get_daily_sentiments('31k24g6himxgznhfccy5a2bgz73y', month)
