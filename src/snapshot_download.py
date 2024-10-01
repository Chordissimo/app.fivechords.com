import huggingface_hub
import logging
import requests
from tqdm.auto import tqdm
from models import _MODELS, _PATHS

class disabled_tqdm(tqdm):
    def __init__(self, *args, **kwargs):
        kwargs["disable"] = True
        super().__init__(*args, **kwargs)

#model_sizes = ["base","small","medium","distil-large-v2","distil-large-v3","large-v3"]
model_sizes = ["distil-large-v2"]

for size in model_sizes:
     repo_id = _MODELS.get(size)
     local_dir = _PATHS.get("model_snapshot") + size
     allow_patterns = [
          "config.json",
          "preprocessor_config.json",
          "model.bin",
          "tokenizer.json",
          "vocabulary.*",
    ]
     kwargs = {
          "local_dir": local_dir,
          "allow_patterns": allow_patterns,
          "tqdm_class": disabled_tqdm,
     }
     
     try:
          huggingface_hub.snapshot_download(repo_id, **kwargs)
     except (
          huggingface_hub.utils.HfHubHTTPError,
          requests.exceptions.ConnectionError,
     ) as exception:
          logger = logging.getLogger("faster_whisper")
          logger.warning(
               "An error occured while synchronizing the model %s from the Hugging Face Hub:\n%s",
               repo_id,
               exception,
          )
