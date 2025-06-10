import logging
import requests

from simap_agent import config

logger = logging.getLogger(__name__)


def post_message(text: str) -> None:
    logger.debug("Sending Slack message")
    response = requests.post(config.SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    logger.debug("Slack response status: %s", response.status_code)
    response.raise_for_status()
