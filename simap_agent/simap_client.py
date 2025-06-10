import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from . import config

logger = logging.getLogger(__name__)


def call(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    url = f"{config.SIMAP_BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.error("Request to %s failed: %s", url, exc)
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON from %s: %s", url, exc)
    return None


def fetch_project_summaries(cpv: List[str], lang: str = "de", max_pages: int = 100) -> List[Dict[str, Any]]:
    summaries: List[Dict[str, Any]] = []
    cursor = None
    for _ in range(max_pages):
        params = {
            "lang": lang,
            "processTypes": "open",
            "cpvCodes": cpv,
            "newestPublicationFrom": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
        }
        if cursor:
            params["lastItem"] = cursor
        data = call(config.SIMAP_SEARCH_ENDPOINT, params)
        if not data or "projects" not in data:
            break
        projects = data["projects"]
        summaries.extend(projects)
        pagination = data.get("pagination", {}) or {}
        cursor = pagination.get("lastItem")
        if not cursor or len(projects) < pagination.get("itemsPerPage", len(projects)):
            break
    logger.info("Fetched %d project summaries", len(summaries))
    return summaries


def fetch_project_details(summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    details: List[Dict[str, Any]] = []
    for s in summaries:
        pid = s.get("id")
        pub = s.get("publicationId")
        if not pid or not pub:
            continue
        endpoint = config.SIMAP_DETAIL_ENDPOINT_TEMPLATE.format(projectId=pid, publicationId=pub)
        data = call(endpoint)
        if data:
            details.append(data)
        time.sleep(0.5)
    logger.info("Fetched details for %d/%d projects", len(details), len(summaries))
    return [d for d in details if d.get("pubType", "").lower() in ("tender", "advance_notice")]
