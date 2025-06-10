import os
from dotenv import load_dotenv

load_dotenv(override=True)

SIMAP_BASE_URL = os.getenv("SIMAP_BASE_URL", "https://simap.ch")
SIMAP_SEARCH_ENDPOINT = os.getenv("SIMAP_SEARCH_ENDPOINT", "/api/publications/v2/project/project-search")
SIMAP_DETAIL_ENDPOINT_TEMPLATE = os.getenv("SIMAP_DETAIL_ENDPOINT_TEMPLATE", "/api/publications/v1/project/{projectId}/publication-details/{publicationId}")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate required variables
_required = {
    'SLACK_WEBHOOK_URL': SLACK_WEBHOOK_URL,
    'OPENAI_API_KEY': OPENAI_API_KEY,
}
_missing = [k for k, v in _required.items() if not v]
if _missing:
    raise EnvironmentError(f"Missing environment variables: {', '.join(_missing)}")
