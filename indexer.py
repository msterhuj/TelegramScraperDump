from typing import List

from telethon import TelegramClient
from telethon.tl.custom.dialog import Dialog
from pymongo import MongoClient
from rich import print
from rich.progress import track
from telethon.tl.types import DocumentAttributeFilename

from config import get_config
conf = get_config()

db = MongoClient(conf.get("mongodb_url"))[conf.get("mongodb_database")]
api_id: int = conf.get("telegram_id")
api_hash: str = conf.get("telegram_hash")


async def index_channels():
    print("Indexing channels...")
    dialogs: List[Dialog] = await client.get_dialogs()
    print(f"Found {len(dialogs)} dialogs")
    # index channels on db
    for dialog in dialogs:
        if not db['channels'].find_one({"id": dialog.id}):
            db['channels'].insert_one({
                "id": dialog.id,
                "title": dialog.title,
                "type": dialog.entity.__class__.__name__.lower(),
                "enabled": False
            })
            print(f"Inserted channel {dialog.title}")


async def index_messages():
    print("Indexing messages...")
    mongo_filter = {"enabled": True, "type": "channel"}
    channels = db['channels'].find(mongo_filter)
    channel_index = 0
    channel_total = db['channels'].count_documents(mongo_filter)
    print(f"Found {channel_total} channels to index")
    for channel in channels:
        channel_index += 1
        print(f"Indexing channel {channel['title']} ({channel_index}/{channel_total})")
        to_insert = []
        total_inserted = 0
        async for message in client.iter_messages(channel["id"]):
            if not db['messages'].find_one({"id": message.id, "channel_id": channel["id"]}):
                data = {
                    "id": message.id,
                    "channel_id": channel["id"],
                    "text": message.message,
                    "date": message.date,
                    "type": message.media.__class__.__name__.lower()
                }
                to_insert.append(data)
                total_inserted += 1
                if len(to_insert) == 250:
                    db['messages'].insert_many(to_insert)
                    print(f"Inserted +{len(to_insert)} messages total: {total_inserted} messages for channel {channel['title']}")
                    to_insert = []
            else:  # index finished to older messages on database
                break
        if to_insert:
            db['messages'].insert_many(to_insert)
            print(
                f"Inserted +{len(to_insert)} messages total: {total_inserted} messages for channel {channel['title']}")


async def index_messages_type_metadata():
    print("Indexing metadata for messages type...")
    mongo_filter_to_update = {'type': 'messagemediadocument', 'mime_type': {'$exists': False}}
    messages = db['messages'].find(filter=mongo_filter_to_update)
    messages_total = db['messages'].count_documents(mongo_filter_to_update)
    print(f"Found {messages_total} metadata messages to index")

    for message in track(messages, total=messages_total):
        telegram_message = await client.get_messages(message["channel_id"], ids=message["id"])
        meta = {}
        if message["type"] == "messagemediadocument":

            meta["mime_type"] = telegram_message.media.document.mime_type
            meta["size"] = telegram_message.media.document.size

            for attr in telegram_message.media.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    meta["filename"] = attr.file_name
            db['messages'].update_one({"id": message["id"], "channel_id": message["channel_id"]}, {"$set": meta})
            print(f"Updated metadata for message {message['id']} on channel {message['channel_id']} with {meta}")


async def main():
    # index channel on db
    await index_channels()
    # index messages per channel enabled on db
    await index_messages()
    # index metadata for messages type (size, type, name)
    await index_messages_type_metadata()


if __name__ == "__main__":
    with TelegramClient('scraper', api_id, api_hash) as client:
        client.loop.run_until_complete(main())
