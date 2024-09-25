import requests
from pytube import Playlist
from links import _LINKS
from datetime import datetime, timedelta
import time
import logging
import sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
stdout = logging.getLogger()
recognizer_endpoint = "http://recognizer:8000/api/recognize/youtube/loader/test"
headers = {
    "Referer": "https://app.fivechords.com",
    "User-Agent": "Links Downloader 1.0"
}

diffs = []

for p in _LINKS:
    playlist = Playlist(p)
    stdout.info("Starting playlist: " + p)

    for url in playlist.video_urls:
        stdout.info("Processing: " + url)
        request_body = {'url': url}
        start = datetime.now()
        
        try:
            response = requests.post(recognizer_endpoint, headers = headers, json = request_body)
            finish = datetime.now()
            diff = finish - start
            diffs.append(diff.total_seconds())
            stdout.info("Status code: " + str(response.status_code) + " , commpleted in: " + str(diff.total_seconds()))
            
        except requests.exceptions.RequestException as err:
            stdout.error(err)
            pass
        
        time.sleep(3)

    stdout.info("Done")

stdout.info("Average processing time: " + str(sum(diffs) / len(diffs)))
