import os
import shutil
import traceback
import uuid
from fastapi import FastAPI, UploadFile, File, \
    HTTPException, Request
from db import database
from helpers.db import DATABASE_COLLECTIONS
from middleware import validate_user_middleware
from models import Response, YoutubeRequest
from services import SpeechRecognizer, \
    ChordsRecognizerChordino, \
    get_samples, resample, get_tempo, \
    download_from_youtube
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlparse
from urllib.parse import parse_qs

DB_NAME = "aichords"

app = FastAPI(title="FiveChords - recognizer",
              docs_url='/adm/recognize',
              openapi_url='/adm/recognize/openapi.json')

origins = ['*']


with open("/etc/auth/auth.conf", "r") as f:
    d = f.read().strip()
    basic_login, basic_password = d.split(":")


@app.middleware("http")
async def validate_user(request: Request, call_next):
    return await validate_user_middleware(
        request=request,
        database=database,
        call_next=call_next
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = "data"

if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)


# @app.get("/health_check", response_model=Response)
# async def health_check() -> Response:
#     return Response(
#         chords=[],
#         text=[],
#         tempo=0.0,
#         duration=0.0
#     )


@app.post("/api/recognize/upload/{task_id}", response_model=Response)
async def recognize(
    request: Request,
    task_id: str,
    file: UploadFile = File(...)
) -> Response:
    user_id = request.state.user_id
    work_dir = os.path.join(DATA_PATH, uuid.uuid4().__str__())
    chord_chunks, tempo = [], 0
    database[DATABASE_COLLECTIONS.RECOGNITIONS.name].insert_one(
        {
            "video_id": None,
            "user_id": user_id,
            "task_id": task_id,
            "completed": False
        })
    try:
        os.mkdir(work_dir)
        filepath = os.path.join(
            work_dir, f"{uuid.uuid4()}.{file.filename.split('.')[-1]}")
        with open(filepath, "wb") as buffer:
            buffer.write(await file.read())
        filepath = resample(filepath, root=work_dir)
        samples = get_samples(filepath=filepath)
        chord_chunks = ChordsRecognizerChordino.recognize(filepath)
        chord_chunks[-1].end = max(int(len(samples) / 16),
                                   chord_chunks[-1].start)

        tempo = get_tempo(samples)
        text_chunks = SpeechRecognizer.recognize(samples)
        if text_chunks and len(text_chunks) > 0:
            if text_chunks[0].start is None:
                text_chunks[0].start = 0
            if text_chunks[-1].end is None:
                text_chunks[-1].end = int(len(samples) / 16000)
        result = {
            "chords": [x.__dict__.copy() for x in chord_chunks],
            "text": [x.__dict__.copy() for x in text_chunks],
            "tempo": tempo,
            "duration": len(samples) / 16000
        }
        database[DATABASE_COLLECTIONS.RECOGNITIONS.name].find_one_and_update(
            filter={
                "user_id": user_id,
                "task_id": task_id
            },
            update={
                "$set": {**result, "completed": True}
            }
        )
        return Response(
            **result
        )
    except SpeechRecognizer.Exception:
        traceback.print_exc()
        result = {
            "chords": [x.__dict__.copy() for x in chord_chunks],
            "text": [],
            "tempo": tempo,
            "duration": len(samples) / 16000
        }
        database[DATABASE_COLLECTIONS.RECOGNITIONS.name].find_one_and_update(
            filter={
                "user_id": user_id,
                "task_id": task_id
            },
            update={
                "$set": {**result, "completed": True}
            }
        )
        return Response(
            **result
        )
    except Exception as e:
        database[DATABASE_COLLECTIONS.RECOGNITIONS.name].find_one_and_delete(
            filter={
                "user_id": user_id,
                "task_id": task_id
            }
        )
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=e.__str__())
    finally:
        if work_dir and os.path.exists(work_dir):
            shutil.rmtree(work_dir)


@app.post("/api/recognize/youtube/loader/{task_id}", response_model=Response)
@app.post("/api/recognize/youtube/{task_id}", response_model=Response)
async def recognize_youtube(
    request: Request,
    task_id: str,
    request_body: YoutubeRequest
) -> Response:
    parsed_url = urlparse(request_body.url)
    video_id = parse_qs(parsed_url.query)["v"][0]
    user_id = request.state.user_id

    database[DATABASE_COLLECTIONS.RECOGNITIONS.name]\
        .insert_one(
        {
            "video_id": video_id,
            "user_id": user_id,
            "task_id": task_id,
            "completed": False
        })

    work_dir = os.path.join(DATA_PATH, uuid.uuid4().__str__())
    chord_chunks, tempo = [], 0
    try:
        os.mkdir(work_dir)
        filepath, captions_qury = await download_from_youtube(
            url=request_body.url, root=work_dir
        )

        filepath = resample(filepath, root=work_dir)
        samples = get_samples(filepath=filepath)
        chord_chunks = ChordsRecognizerChordino.recognize(filepath)
        tempo = get_tempo(samples)
        chord_chunks[-1].end = max(int(len(samples) / 16),
                                   chord_chunks[-1].start)

        model_id = "base" if "/api/recognize/youtube/loader/" not in str(request.url) else "large-v2"
        text_chunks = SpeechRecognizer.recognize(
            samples,
            captions_qury=captions_qury,
            model_id=model_id
        )

        if text_chunks and len(text_chunks) > 0:
            if text_chunks[0].start is None:
                text_chunks[0].start = 0
            if text_chunks[-1].end is None:
                text_chunks[-1].end = int(len(samples) / 16000)
        result = {
            "chords": [x.__dict__.copy() for x in chord_chunks],
            "text": [x.__dict__.copy() for x in text_chunks],
            "tempo": tempo,
            "duration": samples.shape[0] / 16000
        }
        database[DATABASE_COLLECTIONS.RECOGNITIONS.name].find_one_and_update(
            filter={
                "video_id": video_id,
                "user_id": user_id,
                "task_id": task_id
            },
            update={
                "$set": {**result, "completed": True}
            }
        )
        return Response(
            **result
        )

    except SpeechRecognizer.Exception:
        traceback.print_exc()
        result = {
            "chords": [x.__dict__.copy() for x in chord_chunks],
            "text": [],
            "tempo": tempo,
            "duration": samples.shape[0] / 16000
        }
        database[DATABASE_COLLECTIONS.RECOGNITIONS.name].find_one_and_update(
            filter={
                "video_id": video_id,
                "user_id": user_id,
                "task_id": task_id
            },
            update={
                "$set": {**result, "completed": True}
            }
        )
        return Response(
            **result
        )
    except Exception as e:
        database[DATABASE_COLLECTIONS.RECOGNITIONS.name].find_one_and_delete(
            filter={
                "user_id": user_id,
                "task_id": task_id
            }
        )
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=e.__str__())
    finally:
        if work_dir and os.path.exists(work_dir):
            shutil.rmtree(work_dir)
