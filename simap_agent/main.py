import json
import logging
import os
import sys

# Ensure package imports work when executed directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from simap_agent import config
from simap_agent.simap_client import fetch_project_summaries, fetch_project_details
from simap_agent.enricher import enrich_batch
from simap_agent.slack_client import post_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

COMPANY_PROFILE = {
    "name": "Mesoneer GmbH",
    "domains": [
        "Identifikationssoftware",
        "Engineering (Workflow-Automation, RPA, Data Processing, Data-Plattform-Lösungen)",
        "AI & Data (Data Governance, Data Strategy, AI-Anwendungen)",
    ],
    "expertise": [
        "Process automatisation",
        "Data Streaming",
        "Data Plattforms",
        "Workflow Engines",
        "IDP",
        "RPA",
        "Cloud",
        "AI And GenAI",
        "Data Engineering",
        "Data Governance and Strategy",
        "Identification Software",
        "Kyc & Onboarding solutions",
    ],
    "technologies": [
        "BPMN 2.0",
        "Camunda BPM",
        "Axon Ivy",
        "Flowable",
        "Apache Kafka",
        "UiPath",
        "Microsoft Power Automate",
        "Apache",
        "Azure",
        "Python",
        "JAVA",
    ],
    "max_contract_value_eur": 500_000,
}

VALID_CPV = ["48000000", "72000000"]


def main() -> None:
    summaries = fetch_project_summaries(cpv=VALID_CPV)
    details = fetch_project_details(summaries)
    enriched = enrich_batch(details, COMPANY_PROFILE)
    for det, enrich_data in zip(details, enriched):
        title = det.get("project-info", {}).get("title", {}).get("de") or det.get("project-info", {}).get("title", {}).get("fr", "–")
        score = enrich_data.get("apply_score")
        summary = enrich_data.get("summary")
        text = (
            "––––––––––––––––––––––––––––––––––––––––––––––––––\n"
            f":rocket: *Team:* {enrich_data.get('team')}    *# {det.get('projectNumber')}*\n"
            f":file_folder: *Projekt:* {title}\n"
            f":star: *Apply Score:* *{score}*\n\n"
            f":page_facing_up: *Zusammenfassung:*\n>{summary}\n\n"
            f":pushpin: *CPV:* `{(det.get('base') or {}).get('cpvCode', {}).get('code')}`\n"
        )

        qual = enrich_data.get("qualificationCriteria") or []
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
            text += "\n\n"

        award = enrich_data.get("awardCriteria") or []
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

        text += "––––––––––––––––––––––––––––––––––––––––––––––––––"
        print(text)
        #post_message(text)

    with open("enriched_projects.json", "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
