import traceback
from fastapi import FastAPI, \
    HTTPException, Request
from fastapi.responses import RedirectResponse
from db import database
from helpers.db import DATABASE_COLLECTIONS
from middleware import validate_user_middleware
from models import Response, StatusResponse, YoutubeRequest
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlparse
from urllib.parse import parse_qs

DB_NAME = "aichords"

app = FastAPI(title='ProChords',
              docs_url='/api/docs',
              openapi_url='/api/docs/openapi.json')

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


@app.get("/api/health_check", response_model=Response)
async def health_check() -> Response:
    return Response(
        chords=[],
        text=[],
        tempo=0.0,
        duration=0.0
    )


@app.get("/api/status/{task_id}", response_model=StatusResponse)
async def get_status(request: Request, task_id: str) -> StatusResponse:
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


@app.post("/api/youtube/{task_id}", response_model=Response)
async def recognize_youtube(
    request: Request,
    task_id: str,
    request_body: YoutubeRequest
) -> Response:
    parsed_url = urlparse(request_body.url)
    video_id = parse_qs(parsed_url.query)["v"][0]

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
        response = RedirectResponse(
            url=f"https://production.aichords.pro/youtube/{task_id}",
            status_code=307
        )
#        headers = dict(request.headers)
#        for key, value in headers.items():
#            response.headers[key] = value

        return response
    except Exception:
        traceback.print_exc()
