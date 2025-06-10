import requests

from . import config


def post_message(text: str) -> None:
    response = requests.post(config.SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    response.raise_for_status()
