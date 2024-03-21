import json
from fastapi import FastAPI, UploadFile
from src.classes.StreamingHistory import StreamingHistory
from fastapi.middleware.cors import CORSMiddleware
from fastapi.param_functions import File

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

FILES_PATH = 'C:/Users/MaciejŚliwa/PycharmProjects/mgr_backend/data'


# @app.get("/calender/range")
# async def root():
#     streaming_history = StreamingHistory(files_path=FILES_PATH)
#     cal_min, cal_max = streaming_history.get_data_time_range()
#     return {"min": cal_min, "max": cal_max}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/uploadFiles")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    data = json.loads(contents)
    streaming_history = StreamingHistory(file=data, file_type='JSON')
    cal_min, cal_max = streaming_history.get_data_time_range()
    return {"min": cal_min, "max": cal_max}


