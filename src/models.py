from typing import List, Optional
from pydantic import BaseModel
import logging

_LOGGING_LEVEL = logging.DEBUG

_MODELS = {
     "tiny.en": "Systran/faster-whisper-tiny.en",
     "tiny": "Systran/faster-whisper-tiny",
     "base.en": "Systran/faster-whisper-base.en",
     "base": "Systran/faster-whisper-base",
     "small.en": "Systran/faster-whisper-small.en",
     "small": "Systran/faster-whisper-small",
     "medium.en": "Systran/faster-whisper-medium.en",
     "medium": "Systran/faster-whisper-medium",
     "large-v1": "Systran/faster-whisper-large-v1",
     "large-v2": "Systran/faster-whisper-large-v2",
     "large-v3": "Systran/faster-whisper-large-v3",
     "large": "Systran/faster-whisper-large-v3",
     "distil-large-v2": "Systran/faster-distil-whisper-large-v2",
     "distil-medium.en": "Systran/faster-distil-whisper-medium.en",
     "distil-small.en": "Systran/faster-distil-whisper-small.en",
     "distil-large-v3": "Systran/faster-distil-whisper-large-v3",
}

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
