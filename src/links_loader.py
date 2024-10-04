import requests
import time
import logging
import sys

from pytube import Playlist, YouTube
from links import _LINKS
from datetime import datetime, timedelta
from helpers.db import DATABASE_COLLECTIONS
from db import database

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger()
recognizer_endpoint = "http://recognizer:8000/api/recognize/youtube/loader/test"
headers = {
    "Referer": "https://app.fivechords.com",
    "User-Agent": "Links Downloader 1.0"
}


def download():
    diffs = []

    for p in _LINKS:
        playlist = Playlist(p)
        logger.info("Starting playlist: " + p)

        for url in playlist.video_urls:
            logger.info("Processing: " + url)
            request_body = {'url': url}
            start = datetime.now()

            try:
                response = requests.post(recognizer_endpoint, headers = headers, json = request_body)
                finish = datetime.now()
                diff = finish - start
                diffs.append(diff.total_seconds())
                logger.info("Status code: " + str(response.status_code) + " , commpleted in: " + str(diff.total_seconds()))

            except requests.exceptions.RequestException as err:
                logger.error(err)
                pass

        logger.info("Done")

    logger.info("Average processing time: " + str(sum(diffs) / len(diffs)))


def set_title():
    endpoint = "https://www.googleapis.com/youtube/v3/videos"

    all_videos = database[DATABASE_COLLECTIONS.RECOGNITIONS.name].find({})

    if all_videos:
        for video in all_videos:
            not_available = False
            title = ""
            thumbnail = ""
            fields = {}

            try:
                response = requests.get(
                    endpoint,
                    params = {
                        "id": video["video_id"],
                        "part": "snippet",
                        "key": "AIzaSyBrjR0_EvjIsXTz46EjCAewwV2Bs_YOnfA"
                    }
                )
                id = video["video_id"] if video["video_id"] else ""
                url = endpoint + "?id=" + video["video_id"] + "&part=snippet&key=AIzaSyBrjR0_EvjIsXTz46EjCAewwV2Bs_YOnfA"
                if response.status_code != 200:
                    logger.info("Status code: " + str(response.status_code) + ", " + url)
                    continue

                if response:
                    result = response.json()
                    if not result["items"]:
                        not_available = True
                        database[DATABASE_COLLECTIONS.RECOGNITIONS.name].find_one_and_update(
                            filter={
                                "video_id": video["video_id"]
                            },
                            update={
                                "$set": {"delete": True }
                            }
                        )
                        continue

                    if result["items"][0]["snippet"]:
                        if result["items"][0]["snippet"]["title"]:
                            title = result["items"][0]["snippet"]["title"] if not ("title" in video and video["title"] != "") else ""

                        if "default" in result["items"][0]["snippet"]["thumbnails"]:
                            thumbnail = result["items"][0]["snippet"]["thumbnails"]["default"]["url"] if not ("thumbnail" in video and video["thumbnail"] != "") else ""

                    if title != "" and thumbnail != "":
                        fields = {
                            "title": result["items"][0]["snippet"]["title"],
                            "thumbnail": result["items"][0]["snippet"]["thumbnails"]["default"]["url"]
                        }
                    elif title != "" and thumbnail == "":
                        fields = {
                            "title": result["items"][0]["snippet"]["title"]
                        }
                    elif title == "" and thumbnail != "":
                        fields = {
                            "thumbnail": result["items"][0]["snippet"]["thumbnails"]["default"]["url"]
                        }

                    if title != "" or thumbnail != "":
                        database[DATABASE_COLLECTIONS.RECOGNITIONS.name].find_one_and_update(
                            filter={
                                "video_id": video["video_id"]
                            },
                            update={
                                "$set": { **fields }
                            }
                        )

                        logger.info(
                            "not available: " + str(not_available) +
                            ", url: " + "https://youtube.com/watch?v=" + video["video_id"]
                        )
                    else:
                        logger.info(
                            "nothing updated:" +
                            ", url: " + "https://youtube.com/watch?v=" + video["video_id"]
                        )
                else:
                    print(response)

            except requests.exceptions.RequestException as err:
                logger.error(err)
                pass

    else:
        print("no videos found")


set_title()
