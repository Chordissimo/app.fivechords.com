from typing import List, Optional
from pydantic import BaseModel


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
