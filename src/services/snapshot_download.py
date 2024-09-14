import huggingface_hub
import logging
import requests

repo_id = "base"

# _MODELS = {
#     "tiny.en": "Systran/faster-whisper-tiny.en",
#     "tiny": "Systran/faster-whisper-tiny",
#     "base.en": "Systran/faster-whisper-base.en",
#     "base": "Systran/faster-whisper-base",
#     "small.en": "Systran/faster-whisper-small.en",
#     "small": "Systran/faster-whisper-small",
#     "medium.en": "Systran/faster-whisper-medium.en",
#     "medium": "Systran/faster-whisper-medium",
#     "large-v1": "Systran/faster-whisper-large-v1",
#     "large-v2": "Systran/faster-whisper-large-v2",
#     "large-v3": "Systran/faster-whisper-large-v3",
#     "large": "Systran/faster-whisper-large-v3",
#     "distil-large-v2": "Systran/faster-distil-whisper-large-v2",
#     "distil-medium.en": "Systran/faster-distil-whisper-medium.en",
#     "distil-small.en": "Systran/faster-distil-whisper-small.en",
#     "distil-large-v3": "Systran/faster-distil-whisper-large-v3",
# }

allow_patterns = [
        "config.json",
        "preprocessor_config.json",
        "model.bin",
        "tokenizer.json",
        "vocabulary.*",
    ]

kwargs = {
    "local_dir": "data",
    "allow_patterns": allow_patterns,
    "tqdm_class": disabled_tqdm,
}

try:
    huggingface_hub.snapshot_download(repo_id, **kwargs)
except (
    huggingface_hub.utils.HfHubHTTPError,
    requests.exceptions.ConnectionError,
) as exception:
    logger = get_logger()
    logger.warning(
        "An error occured while synchronizing the model %s from the Hugging Face Hub:\n%s",
        repo_id,
        exception,
    )
