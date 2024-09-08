from dataclasses import dataclass
from typing import List, Optional
# import autochord
from chord_extractor.extractors import Chordino
from abc import ABC, abstractmethod


class ChordsRecognizer(ABC):

    @classmethod
    def recognize(cls, filepath: str) -> List["ChordsRecognizer.Chunk"]:
        pass

    @dataclass
    class Chunk:
        chord: str
        start: int  # milliseconds
        end: int    # milliseconds
    
    class Exception(Exception):
        def __init__(self, message: str) -> None:
            self.message = message
            super().__init__()
        
        def __str__(self) -> str:
            return f"ChordsRecognizer.Exception: {self.message}"


class ChordsRecognizerChordino(ChordsRecognizer):

    __initialized: bool = False
    __model: Optional[Chordino] = None

    @classmethod
    def __init_if_needed(cls) -> None:
        if cls.__initialized:
            return
        cls.__model = Chordino(roll_on=1)
        cls.__initialized = True

    @classmethod
    def recognize(cls, filepath: str) -> List[ChordsRecognizer.Chunk]:
        cls.__init_if_needed()
        try:
            chords = cls.__model.extract(filepath)
            result = []
            last_start = -1
            for x in chords[::-1]:
                start = int(x.timestamp * 1000)
                result.insert(0, ChordsRecognizer.Chunk(
                    chord=x.chord,
                    start=start,
                    end=last_start
                ))
                last_start = start
            return result
        
        except Exception as e:
            raise ChordsRecognizer.Exception(message=e.__str__())

class ChordsRecognizerAutochord(ChordsRecognizer):
    
    @classmethod
    def recognize(cls, filepath: str) -> List[ChordsRecognizer.Chunk]:
        try:
            # result = autochord.recognize(filepath, lab_fn="chords.lab")
            # return [
            #     ChordsRecognizer.Chunk(
            #         chord=x[2],
            #         start=int(x[0] * 1000),
            #         end=int(x[1] * 1000)
            #     ) for x in result
            # ]
            return []
        except Exception as e:
            raise ChordsRecognizer.Exception(message=e.__str__())

    
