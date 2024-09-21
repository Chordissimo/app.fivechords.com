import requests
from links import _LINKS

for url in links:
    #id = url.split("?")[-1].split("&")[0].split("=")[1]
    recognizer_endpoint = "http://recognizer:8000/api/recognize/youtube/loader/test"
    # retriever_endpoint = "http://retriever:8002/api/retrieve/youtube/test"
    request_body = {'url': url}
    headers = {"Referer": "https://app.fivechords.com"}
    response = requests.post(recognizer_endpoint, headers = headers, json = request_body)
    print(response)
