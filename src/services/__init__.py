from pytube import YouTube, CaptionQuery
import uuid
import librosa
# from .speech_recognizer import SpeechRecognizer
from .speech_recognizer_v2 import SpeechRecognizerFaster as SpeechRecognizer
import asyncio
from os import PathLike
import os
from typing import Any, Tuple
from models import _LOGGING_LEVEL

import numpy as np
from .chord_recognizer import ChordsRecognizer, ChordsRecognizerAutochord, \
    ChordsRecognizerChordino

import logging
import sys

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=_LOGGING_LEVEL,
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger()

MAX_SECONDS = 6000


class FileReadingException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__()

    def __str__(self) -> str:
        return f"FileReadingException: {self.message}"


def on_dowload_complete(f: asyncio.Future, url: str, y: Any):
    logger.info("on_dowload_complete: " + url)
    f.set_result(url)


async def download_from_youtube(
        url: str,
        root: str
) -> Tuple[PathLike, CaptionQuery]:
    future = asyncio.Future()
    yt = YouTube(url=url, on_complete_callback=lambda y, x: on_dowload_complete(f=future, url=x, y=y))
    # assert yt.length <= MAX_SECONDS
    
    yt.streams.filter(only_audio=True).first().download(root, filename=f"{uuid.uuid4().__str__()}.mp4")
    
    await future
    return future.result(), yt.captions


def resample(filepath: PathLike, root: str) -> PathLike:
    resampled_filepath = os.path.join(root, f"{uuid.uuid4().__str__()}.wav")
    ex = f"ffmpeg -i {filepath} -ar 16000 -ac 1 -y {resampled_filepath} > /dev/null 2>&1"
    os.system(ex)
    return resampled_filepath


def get_100_samples_per_second(wave: np.ndarray) -> np.ndarray:
    return librosa.resample(y=wave, orig_sr=16000, target_sr=100)


def check_samples_size(samples: np.ndarray):
    assert samples.shape[0] <= (MAX_SECONDS * 16000)


def get_samples(filepath: PathLike) -> np.ndarray:
    samples, _ = librosa.load(filepath, sr=16000)
    check_samples_size(samples=samples)
    return samples


def get_tempo(samples: np.ndarray) -> float:
    return librosa.feature.tempo(y=samples, sr=16000).item()


__all__ = [
    "ChordsRecognizer", "SpeechRecognizer",
    "ChordsRecognizerAutochord", "ChordsRecognizerChordino",
    "resample", "get_samples", "get_tempo",
    "download_from_youtube", "get_100_samples_per_second", "check_samples_size"
]
