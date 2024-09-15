import requests
import time

links = [
    "https://www.youtube.com/watch?v=eVli-tstM5E&list=PLyORnIW1xT6wqvszJbCdLdSjylYMf3sNZ&index=1&pp=iAQB8AUB",
    "https://www.youtube.com/watch?v=q3zqJs7JUCQ&list=PLyORnIW1xT6wqvszJbCdLdSjylYMf3sNZ&index=2&pp=iAQB8AUB",
    "https://www.youtube.com/watch?v=IXJTaHySW8I&list=PLyORnIW1xT6wqvszJbCdLdSjylYMf3sNZ&index=3&pp=iAQB8AUB",
    "https://www.youtube.com/watch?v=Oa_RSwwpPaA&list=PLyORnIW1xT6wqvszJbCdLdSjylYMf3sNZ&index=4&pp=iAQB8AUB",
    "https://www.youtube.com/watch?v=huGd4efgdPA&list=PLyORnIW1xT6wqvszJbCdLdSjylYMf3sNZ&index=5&pp=iAQB8AUB",
    "https://www.youtube.com/watch?v=o3IlfLsaU28&list=PLyORnIW1xT6wqvszJbCdLdSjylYMf3sNZ&index=6&pp=iAQB8AUB"
]

for url in links:
    #id = url.split("?")[-1].split("&")[0].split("=")[1]
    endpoint = "https://app.fivechords.com/api/recognize/youtube/test"
    request_body = {'url': url}
    headers = {"Referer": "https://app.fivechords.com"}
    response = requests.post(endpoint, headers = headers, json = request_body)
    print(response)
    time.sleep(3)
