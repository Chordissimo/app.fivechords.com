from faster_whisper import WhisperModel
import numpy as np
from models import _MODELS
import logging
import sys

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=_LOGGING_LEVEL,
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger()

class FasterWhisperWhithLanguageDetection(WhisperModel):
    def detect_language(self, audio: np.ndarray) -> str:
        features = self.feature_extractor(audio, chunk_length=None)
        language_detection_segments = 1
        start_timestamp = 0
        content_frames = (
            features.shape[-1] - self.feature_extractor.nb_max_frames
        )
        seek = (
            int(start_timestamp * self.frames_per_second)
            if start_timestamp * self.frames_per_second < content_frames
            else 0
        )
        end_frames = min(
            seek
            + self.feature_extractor.nb_max_frames
            * language_detection_segments,
            content_frames,
        )

        while seek < end_frames:
            segment = features[
                :, seek: seek + self.feature_extractor.nb_max_frames
            ]

            encoder_output = self.encode(segment)
            # results is a list of tuple[str, float] with language names and
            # probabilities.
            results = self.model.detect_language(encoder_output)[0]
            # Parse language names to strip out markers
            all_language_probs = [
                (token[2:-2], prob) for (token, prob) in results
            ]

            # Get top language token and probability
            language, language_probability = all_language_probs[0]
            if language_probability >= 0.5:
                break
            seek += segment.shape[-1]

        return language
