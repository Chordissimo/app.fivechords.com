from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import torch
from transformers import AutoModelForSpeechSeq2Seq, \
    AutoProcessor, pipeline, Pipeline
from pytube import CaptionQuery, Caption
import re


class SpeechRecognizer:
    __initialized = False
    __pipe: Optional[Pipeline] = None
    __device: Optional[torch.device] = None

    @classmethod
    def __init_if_needed(cls):
        if cls.__initialized:
            return
        cls.__device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() \
            else torch.float32

        model_id = "openai/whisper-base"

        cls.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True
        )
        cls.model.to(cls.__device)

        cls.processor = AutoProcessor.from_pretrained(model_id)

        cls.__pipe = pipeline(
            "automatic-speech-recognition",
            model=cls.model,
            tokenizer=cls.processor.tokenizer,
            feature_extractor=cls.processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=16,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=cls.__device
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
    ) -> List["SpeechRecognizer.Chunk"]:
        events = caption.json_captions["events"]
        return [SpeechRecognizer.Chunk(
            text=SpeechRecognizer.clean_text(x["segs"][0]["utf8"])
            if len(x["segs"]) > 0 else "",
            start=x["tStartMs"],
            end=(x["tStartMs"] + x["dDurationMs"])
        ) for x in events]

    @classmethod
    def recognize(
            cls,
            samples: np.ndarray,
            captions_qury: Optional[CaptionQuery] = None
    ) -> List["SpeechRecognizer.Chunk"]:
        try:
            cls.__init_if_needed()
            language_code = None
            if captions_qury is not None and len(captions_qury) > 0:
                if len(captions_qury) == 1:
                    return SpeechRecognizer.generate_from_caption(
                        captions_qury.all()[0]
                    )
                input_features = cls.processor(
                    samples,
                    return_tensors="pt",
                    sampling_rate=16000
                ).input_features
                lang_token = cls.model.generate(
                    input_features,
                    max_new_tokens=1
                )[0, 1]

                language_code = cls.processor.tokenizer.decode(lang_token)
                language_code = language_code.replace(
                    "<|", "").replace("|>", "")
                caption = next(
                    (x for x in captions_qury.all()
                     if language_code in x.code),
                    None
                )
                if caption is not None:
                    return SpeechRecognizer.generate_from_caption(caption)

            result = cls.__pipe(
                samples,
                return_timestamps="word",
                generate_kwargs={"language": language_code}
                if language_code is not None else {}
            )

            return [
                SpeechRecognizer.Chunk(
                    text=x["text"],
                    start=int(x["timestamp"][0] *
                              1000) if x["timestamp"][0] else None,
                    end=int(x["timestamp"][1] *
                            1000) if x["timestamp"][1] else None
                ) for x in result["chunks"]
            ]
        except Exception as e:
            raise SpeechRecognizer.Exception(message=e.__str__())

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
