from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import torch
from pytube import CaptionQuery, Caption
import re

from services.faster_whisper_extention import \
    FasterWhisperWhithLanguageDetection


class SpeechRecognizerFaster:
    __initialized = False
    model: Optional[FasterWhisperWhithLanguageDetection] = None
    __device: Optional[torch.device] = None

    @classmethod
    def __init_if_needed(cls):
        if cls.__initialized:
            return
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = "float16" if torch.cuda.is_available() \
            else "float32"
        dtype = "float32"
        model_id = "base"
        cls.model = FasterWhisperWhithLanguageDetection(
            model_id,
            device=device,
            compute_type=dtype
        )

    @staticmethod
    def clean_text(x: str) -> str:
        pattern = r'\([^)]*\)|\{[^}]*\}|\[[^\]]*\]'
        return re.sub(
            pattern, '', x.replace("♪", "").replace("\n", " ")).strip()

    @classmethod
    def generate_from_caption(
        cls,
        caption: Caption
    ) -> List["SpeechRecognizerFaster.Chunk"]:
        events = caption.json_captions["events"]
        return [SpeechRecognizerFaster.Chunk(
            text=SpeechRecognizerFaster.clean_text(x["segs"][0]["utf8"])
            if len(x["segs"]) > 0 else "",
            start=x["tStartMs"],
            end=(x["tStartMs"] + x["dDurationMs"])
        ) for x in events]

    @classmethod
    def recognize(
            cls,
            samples: np.ndarray,
            captions_qury: Optional[CaptionQuery] = None
    ) -> List["SpeechRecognizerFaster.Chunk"]:
        try:
            cls.__init_if_needed()
            language_code = cls.model.detect_language(audio=samples)
            print("language_code", language_code)
            if captions_qury is not None and len(captions_qury) > 0:
                if len(captions_qury) == 1:
                    return SpeechRecognizerFaster.generate_from_caption(
                        captions_qury.all()[0]
                    )
                caption = next(
                    (x for x in captions_qury.all()
                     if language_code in x.code),
                    None
                )
                if caption is not None:
                    return SpeechRecognizerFaster.generate_from_caption(
                        caption
                    )

            segments, _ = cls.model.transcribe(
                samples,
                language=language_code,
                condition_on_previous_text=False,
                word_timestamps=True,
            )

            return [
                SpeechRecognizerFaster.Chunk(
                    text=x.word,
                    start=int(x.start *
                              1000) if x.start is not None else None,
                    end=int(x.end *
                            1000) if x.end is not None else None
                ) for segment in segments for x in segment.words
            ]
        except Exception as e:
            raise SpeechRecognizerFaster.Exception(message=e.__str__())

    @dataclass
    class Chunk:
        text: str
        start: Optional[int]  # milliseconds
        end: Optional[int]    # milliseconds

    class Exception(Exception):
        def __init__(self, message: str) -> None:
            self.message = message
            super().__init__()

        def __str__(self) -> str:
            return f"SpeechRecognizer.Exception: {self.message}"
