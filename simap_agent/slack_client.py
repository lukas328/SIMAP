import logging
from datetime import datetime
from typing import Any, Dict, List

import requests

from simap_agent import config

logger = logging.getLogger(__name__)


def fmt_date(value: str | None, fmt: str) -> str:
    """Return formatted date or fallback."""
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime(fmt)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d").strftime(fmt)
        except ValueError:
            return value


def format_slack_blocks(proj: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return Slack blocks for a project dictionary."""
    team = proj.get("team")
    pr = proj.get("project", {})
    title = pr.get("title_de", "—")
    customer = pr.get("customer", "—")
    score = proj.get("apply_score", 0)
    summary = proj.get("summary", "—")
    project_number = pr.get("projectNumber", "—")
    project_id = pr.get("projectId", "—")
    offer_dl_raw = pr.get("offerDeadline")
    start_raw = pr.get("contract_start")
    qa_dl_raw = pr.get("qna_deadline")
    cpv = pr.get("cpvCode", {}) or {}
    cpv_code = cpv.get("code", "—")
    cpv_label = cpv.get("label_de", "—")
    missing = proj.get("missing_info") or []
    missing_str = ", ".join(missing) if missing else "Keine"

    offer_dl = fmt_date(offer_dl_raw, "%d.%m.%Y")
    qa_dl = fmt_date(qa_dl_raw, "%d.%m.%Y")
    start = fmt_date(start_raw, "%d.%m.%Y")

    text = (
        f"\n:rocket: *Team: {team}*  *#{project_number}*\n"
        f"\n:file_folder: *Projekt:* {title} / {customer}\n"
        f"\n:star: *Apply Score:* *{score}*\n"
        f"\n:page_facing_up: *Zusammenfassung:*\n>{summary}\n\n"
        f":calendar:   •   *Q&A:* {qa_dl}   •   *Frist:* {offer_dl}   •   *Start:* {start} \n"
        f"\n:pushpin: *CPV:* `{cpv_code}` – {cpv_label}\n"
        f"\n:mag: *Fehlende Infos:* {missing_str}\n"
    )

    qual = proj.get("qualificationCriteria") or []
    if qual:
        text += ":bookmark_tabs: *Eignungskriterien:*"
        for c in qual:
            title = (c.get("title") or {}).get("de")
            if not title:
                continue
            desc = (c.get("description") or {}).get("de") or ""
            text += f"\n• *{title}*"
            if desc:
                text += f" – {desc}"
        text += "\n"

    award = proj.get("awardCriteria") or []
    if award:
        text += ":trophy: *Zuschlagskriterien:*"
        for a in award:
            title = (a.get("title") or {}).get("de")
            if not title:
                continue
            weight = a.get("weighting")
            text += f"\n• *{title}*"
            if weight is not None:
                text += f" – Gewichtung {weight}%"
        text += "\n"

    blocks = [
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": text}},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"<https://www.simap.ch/de/project-detail/{project_id}#ausschreibung|🔗 Vollständige Ausschreibung>"
                }
            ],
        },
        {"type": "divider"},
    ]
    return blocks


def post_blocks(blocks: List[Dict[str, Any]]) -> None:
    """Send Slack message blocks."""
    logger.debug("Sending Slack blocks")
    payload = {"blocks": blocks}
    response = requests.post(
        config.SLACK_WEBHOOK_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    logger.debug("Slack response status: %s", response.status_code)
    response.raise_for_status()


def post_message(text: str) -> None:
    logger.debug("Sending Slack message")
    response = requests.post(config.SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    logger.debug("Slack response status: %s", response.status_code)
    response.raise_for_status()
