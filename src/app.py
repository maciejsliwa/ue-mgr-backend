from fastapi import FastAPI
from src.classes.StreamingHistory import StreamingHistory
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FILE_PATH = 'C:/Users/MaciejŚliwa/PycharmProjects/mgr_backend/data/Streaming_History_Audio_2023_5.json'


@app.get("/calender/range")
async def root():
    streaming_history = StreamingHistory(file_path=FILE_PATH)
    cal_min, cal_max = streaming_history.get_data_time_range()
    return {"min": cal_min, "max": cal_max}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
