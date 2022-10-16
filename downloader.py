import os

from telethon import TelegramClient
from pymongo import MongoClient
from rich import print
from rich.progress import track

from config import get_config
conf = get_config()

db = MongoClient(conf.get("mongodb_url"))[conf.get("mongodb_database")]
api_id: int = conf.get("telegram_id")
api_hash: str = conf.get("telegram_hash")

to_download_filter = conf.get("mongodb_download_filter")
to_download_total = db['messages'].count_documents(to_download_filter)
to_download = db['messages'].find(to_download_filter)
download_dir = conf.get("download_dir")
print(f"Download filter: {to_download_filter}")
print("Total files match to download filter: ", to_download_total)


async def main():
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)

    for message in track(to_download, total=to_download_total):
        telegram_message = await telegram.get_messages(message['channel_id'], ids=message['id'])
        filename = message["filename"]
        new_filename = f"{message['channel_id']}-{message['id']}-{filename}"
        if not os.path.exists(f"{download_dir}/{new_filename}"):
            print(f"Downloading file {filename} size {message['size']}")
            await telegram_message.download_media(f"{download_dir}/{new_filename}")
        else:
            print(f"File {filename} already downloaded")

if __name__ == "__main__":
    with TelegramClient('scraper', api_id, api_hash) as telegram:
        telegram.loop.run_until_complete(main())
