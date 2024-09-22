import requests
from pytube import Playlist
from links import _LINKS
from datetime import datetime, timedelta
import time
import random

stdlog = log.getLogger ('stdout')
recognizer_endpoint = "http://recognizer:8000/api/recognize/youtube/loader/test"
headers = {"Referer": "https://app.fivechords.com"}

diffs = []

for p in _LINKS:
    playlist = Playlist(p)
    stdout.info("Starting playlist: " + p)
    
    for url in playlist.video_urls[:3]:
        request_body = {'url': url}
        start = datetime.now()
        time.sleep(random.randint(1, 5))
        # response = requests.post(recognizer_endpoint, headers = headers, json = request_body)
        finish = datetime.now()
        diff = finish - start
        diffs.append(diff)
        # stdout.info("Status code: " + response.status_code + " , commpleted in: ", diff.total_seconds())
        stdout.info("Status code: 200, commpleted in: ", diff.total_seconds())

stdout.info("Done. Average processing time: " + sum(diffs) / len(diffs))
