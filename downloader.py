import os
import re
import sys
import time

from curl_cffi import requests

pat = re.compile(
    r'<a\b[^>]*\bdata-id=["\'](\d+)["\'][^>]*>.*?'
    r'<span[^>]*class=["\'][^"\']*chapter-item__name[^"\']*["\'][^>]*>(.*?)</span>.*?</a>',
    re.I | re.S,
)
urls = []
for item in sys.argv[1:]:
    if item == "--help":
        print("Usage: python downloader.py <?list.txt> <https://manhwaread.com/manhwa/...>")
        sys.exit(0)
    if item.startswith("https://manhwaread.com"):
        urls.append(item)
    elif "http" not in item:
        try:
            with open(item, "r", encoding="utf-8") as f:
                for url in f.read().splitlines():
                    if (u := url.strip()) and u.startswith("https://manhwaread.com"):
                        urls.append(u)
        except Exception:
            pass

if not urls:
    url = input("No URL found. Please provide one manually: ")
    if url.startswith("https://manhwaread.com"):
        urls.append(url)
    else:
        print("Invalid URL provided")
        sys.exit(0)
urls = list(dict.fromkeys(urls).keys())


def download_image(image_url, origin_site_url, output_filename, timeout=60):
    headers = {
        "Referer": origin_site_url,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6045.199 Safari/537.36",
    }

    try:
        response = requests.get(image_url, headers=headers, impersonate="chrome120", timeout=timeout)

        if response.status_code == 200:
            with open(output_filename, "wb") as f:
                f.write(response.content)
            print(f"Downloaded: {output_filename}")
            return response.status_code
        else:
            print(f"Failure. Server returned code: {response.status_code}")
            print(f"Server response: {response.text[:200]}")
            return response.status_code

    except Exception as e:
        print(f"An error occured : {e}")


for url in urls:
    c = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6045.199 Safari/537.36",
        },
        impersonate="chrome120",
    ).text
    name = c.split('"og:title" content="')[1].split(" - #")[0].replace("&#039;", "'")
    book_id = c.split(" - #")[1].split(" -")[0]
    chapters = [m[0] for m in pat.findall(c)][2:]

    check = input(f"Will download: {name} ({book_id}). This manhwaread has {len(chapters)} chapters. Are you sure? [Y/n]")
    if check.lower() in ("n", "no", "please no!", "stop this", "wtf"):
        continue

    os.makedirs(name, exist_ok=True)
    for chapter, id in enumerate(chapters, start=1):
        path = os.path.join(name, str(chapter).zfill(2))
        os.makedirs(path, exist_ok=True)
        for i in range(1, 1000):
            id_image = str(i).zfill(3)
            url = f"https://manread.xyz/{book_id}/{id}/mr_{id_image}.jpg"
            resp = download_image(url, "https://manhwaread.com/", os.path.join(path, f"{id_image}.jpg"))
            if resp == 404:
                print("Downloaded chapter", chapter)
                break
            elif resp != 200:
                print("Retrying in 20 seconds.")
                time.sleep(20)
                resp = download_image(url, "https://manhwaread.com/", os.path.join(path, f"{id_image}.jpg"))
                if resp == 404:
                    print("Downloaded chapter", chapter)
                    break
                elif resp != 200:
                    print("Retrying in 2 minutes.")
                    time.sleep(120)
                    resp = download_image(url, "https://manhwaread.com/", os.path.join(path, f"{id_image}.jpg"))
                    if resp == 404:
                        print("Downloaded chapter", chapter)
                        break
            time.sleep(0.5)
