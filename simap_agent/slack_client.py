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

    qual_summary = proj.get("qualificationCriteriaSummary")
    qual = proj.get("qualificationCriteria") or []
    qual_in_docs = str(proj.get("qualificationCriteriaInDocuments", "")).lower() == "yes" or proj.get("qualificationCriteriaInDocuments") is True

    qual_as_pdf = str(proj.get("qualificationCriteriaAsPDF", "")).lower() == "yes" or proj.get("qualificationCriteriaAsPDF") is True
    if qual_summary:
        text += f"\n:bookmark_tabs: *Eignungskriterien:*\n{qual_summary}\n"
    elif qual:
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

    else:
        if qual_as_pdf:
            text += ":bookmark_tabs: Kriterien sind als pdf hinterlegt\n"
        elif qual_in_docs:

            text += ":bookmark_tabs: Kriterien sind in den Dokumenten hinterlegt\n"

    award_summary = proj.get("awardCriteriaSummary")
    award = proj.get("awardCriteria") or []
    award_in_docs = str(proj.get("awardCriteriaInDocuments", "")).lower() == "yes" or proj.get("awardCriteriaInDocuments") is True

    award_as_pdf = str(proj.get("awardCriteriaAsPDF", "")).lower() == "yes" or proj.get("awardCriteriaAsPDF") is True
    if award_summary:
        text += f"\n:trophy: *Zuschlagskriterien:*\n{award_summary}\n"
    elif award:
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

    else:
        if award_as_pdf:
            text += ":trophy: Kriterien sind als pdf hinterlegt\n"
        elif award_in_docs:

            text += ":trophy: Kriterien sind in den Dokumenten hinterlegt\n"

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
    # Extract fallback text for clients that do not support blocks.
    fallback = ""
    for block in blocks:
        if block.get("type") == "section" and block.get("text"):
            fallback = block["text"].get("text", "")
            break
    payload = {"text": fallback[:150], "blocks": blocks}
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
