import base64
import crypt
import os
import shutil
import traceback
from typing import List, Optional
import uuid
from fastapi import FastAPI, UploadFile, File, \
    HTTPException, Request, status, Response as NativeResponse
from pydantic import BaseModel
from helpers.db import DATABASE_COLLECTIONS
from helpers.users import get_user_by_token, update_users_token
from services import SpeechRecognizer, \
    ChordsRecognizerChordino, \
    get_samples, resample, get_tempo, \
    download_from_youtube
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin._token_gen import ExpiredIdTokenError
from pymongo.mongo_client import MongoClient
from urllib.parse import urlparse
from urllib.parse import parse_qs

DB_NAME = "aichords"

app = FastAPI(docs_url="/docs")

# uri = "mongodb+srv://8444691:AkdbWtQObE6IgKY7@chord-api.lc5insj.mongodb.net/"
# uri += "?retryWrites=true&w=majority&appName=chord-api"

uri = "mongodb://aichords:12345@mongo:27017/aichords"

mongodb_client = MongoClient(uri)
database = mongodb_client[DB_NAME]


origins = ['*']


cred = credentials.Certificate("/etc/auth/prochords.json")
firebase_admin.initialize_app(cred)


with open("/etc/auth/auth.conf", "r") as f:
    d = f.read().strip()
    basic_login, basic_password = d.split(":")


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    if "/docs" in str(request.url) or "openapi.json" in str(request.url):
        return await call_next(request)
    token = request.headers.get("Authorization", None)
    user_id = None

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="")
    if token and token.startswith("Basic"):
        id_token = token.split(" ").pop()
        decoded_credentials = base64.b64decode(id_token).decode("utf-8")
        username, password = decoded_credentials.split(":")
        assert username == basic_login
        hashed_input_password = crypt.crypt(password, basic_password)
        assert hashed_input_password == basic_password
        user_id = "test"
    else:
        try:
            id_token = token.split(" ").pop()
            user = get_user_by_token(database=database, token=id_token)
            if user is None:
                decoded_token = auth.verify_id_token(id_token)
                uid = decoded_token.get("uid")
                exp = decoded_token.get("exp")
                update_users_token(
                    database=database,
                    user_id=uid,
                    token=id_token,
                    exp=exp
                )
                user_id = uid
            else:
                user_id = user["user_id"]

        except ExpiredIdTokenError:
            traceback.print_exc()
            raise HTTPException(status_code=403)
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=e.__str__())
    assert user_id is not None
    request.state.user_id = user_id
    response = await call_next(request)
    return response

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


class Chord(BaseModel):
    chord: str
    start: int  # milliseconds
    end: int    # milliseconds


class TextStr(BaseModel):
    text: str
    start: Optional[int]  # milliseconds
    end: Optional[int]    # milliseconds


class Response(BaseModel):
    chords: List[Chord]
    text: Optional[List[TextStr]]
    tempo: float
    duration: float


class YoutubeRequest(BaseModel):
    url: str


class StatusResponse(BaseModel):
    found: bool
    completed: bool
    result: Optional[Response]


@app.get("/api/health_check", response_model=Response)
async def health_check() -> Response:
    return Response(
        chords=[],
        text=[],
        tempo=0.0,
        duration=0.0
    )


@app.post("/upload/{task_id}", response_model=Response)
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


@app.post("/youtube/{task_id}", response_model=Response)
async def recognize_youtube(
    request: Request,
    task_id: str,
    request_body: YoutubeRequest
) -> Response:
    parsed_url = urlparse(request_body.url)
    video_id = parse_qs(parsed_url.query)["v"][0]
    user_id = request.state.user_id

    try:
        result = database[DATABASE_COLLECTIONS.RECOGNITIONS.name].find_one({
            "video_id": video_id,
            "completed": True
        })
        if result:
            return Response(
                chords=result["chords"],
                text=result["text"],
                tempo=result["tempo"],
                duration=result["duration"]
            )
    except Exception:
        traceback.print_exc()

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

        text_chunks = SpeechRecognizer.recognize(
            samples,
            captions_qury=captions_qury
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


@app.get("/status/{task_id}", response_model=StatusResponse)
async def get_status(
    request: Request,
    response: NativeResponse, task_id: str
) -> StatusResponse:
    try:
        user_id = request.state.user_id
        result = database[DATABASE_COLLECTIONS.RECOGNITIONS.name].find_one({
            "user_id": user_id, "task_id": task_id
        })
        if result is None or "completed" not in result:
            return StatusResponse(
                found=False,
                completed=False,
                result=None
            )

        if not result["completed"]:
            response.status_code = status.HTTP_202_ACCEPTED
            return StatusResponse(
                found=True,
                completed=False,
                result=None
            )

        return StatusResponse(
            found=True,
            completed=True,
            result=Response(
                chords=result["chords"],
                text=result["text"],
                tempo=result["tempo"],
                duration=result["duration"]
            )
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=e.__str__())

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000, workers=2)
