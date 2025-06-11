"""Load configuration from the environment."""

import os
import json
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv(override=True)
logger.debug("Environment variables loaded")

# Base URL and endpoints for SIMAP
SIMAP_BASE_URL = os.getenv("SIMAP_BASE_URL", "https://simap.ch")
SIMAP_SEARCH_ENDPOINT = os.getenv(
    "SIMAP_SEARCH_ENDPOINT", "/api/publications/v2/project/project-search"
)
SIMAP_DETAIL_ENDPOINT_TEMPLATE = os.getenv(
    "SIMAP_DETAIL_ENDPOINT_TEMPLATE",
    "/api/publications/v1/project/{projectId}/publication-details/{publicationId}",
)
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    "https://dataai-opai-openai-weu-001.cognitiveservices.azure.com/",
)
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION", "2025-01-01-preview")
COMPANY_PROFILE_FILE = os.getenv("COMPANY_PROFILE_FILE", "company_profile.json")
CPV_CODES = os.getenv("CPV_CODES", "48000000,72000000").split(",")
# Minimum apply score required for posting a project to Slack
APPLY_SCORE_THRESHOLD = int(os.getenv("APPLY_SCORE_THRESHOLD", "7"))
logger.debug("Slack webhook configured: %s", bool(SLACK_WEBHOOK_URL))

try:
    with open(COMPANY_PROFILE_FILE, "r", encoding="utf-8") as f:
        COMPANY_PROFILE = json.load(f)
    logger.debug("Company profile loaded from %s", COMPANY_PROFILE_FILE)
except FileNotFoundError:
    logger.warning("Company profile file %s not found", COMPANY_PROFILE_FILE)
    COMPANY_PROFILE = {}

# Validate required variables
_required = {
    'SLACK_WEBHOOK_URL': SLACK_WEBHOOK_URL,
    'OPENAI_API_KEY': OPENAI_API_KEY,
}
_missing = [k for k, v in _required.items() if not v]
if _missing:
    raise EnvironmentError(f"Missing environment variables: {', '.join(_missing)}")
