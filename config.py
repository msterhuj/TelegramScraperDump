import os

import yaml

from rich.traceback import install

install(show_locals=True)

default_example_config = {
    "mongodb_url": "mongodb://localhost:27017",
    "mongodb_database": "telegram",
    "mongodb_download_filter": {
        'type': 'messagemediadocument',
        'mime_type': 'text/plain',
        'size': {
            '$gte': 0,
            '$lt': 1000  # 1kb
        }
    },
    "telegram_id": 12345678,
    "telegram_hash": "0123456789abcdef0123456789abcdef",
    "download_dir": "downloads"
}

if not os.path.exists("config.yaml"):
    with open("config.yaml", "w") as stream:
        yaml.dump(default_example_config, stream)
    print("Initial config.yaml created, please fill it with your data and rerun the script")
    exit(1)


def get_config() -> dict:
    with open("config.yaml", "r") as stream:
        return yaml.load(stream, Loader=yaml.FullLoader)


if __name__ == '__main__':
    print("Please, configure the config.yaml file before running the script")
    print("You can get your Telegram API ID and API HASH from https://my.telegram.org/apps")
    print("Then run indexer.py or downloader.py")
