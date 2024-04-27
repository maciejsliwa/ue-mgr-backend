import json
from fastapi import FastAPI, UploadFile, BackgroundTasks, Depends, HTTPException, status
from src.classes.DatabaseContext import DatabaseContext
from fastapi.middleware.cors import CORSMiddleware
from fastapi.param_functions import File
from pydantic import BaseModel
import spotipy
from fastapi.security import OAuth2PasswordBearer
from src.classes.StreamingHistory import StreamingHistory

app = FastAPI()

origins = [
    "http://localhost:3000/",
    "localhost:3000/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
db = DatabaseContext()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

class Token(BaseModel):
    token: str


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
async def get_range(token: str = Depends(oauth2_scheme)):
    sp = spotipy.Spotify(auth=token)
    user = sp.current_user()
    username = user['id']
    min, max = db.get_data_time_range(username)
    return {"min": min, "max": max}

@app.get("/getLast")
async def get_recently_played(token: str = Depends(oauth2_scheme)):
    sp = spotipy.Spotify(auth=token)
    user = sp.current_user()
    username = user['id']
    return {"recently_played": db.get_last_played_track(username)}


