import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
from openai import OpenAI

load_dotenv(override=True)
# Configuration from environment variables
SIMAP_BASE_URL = os.getenv("SIMAP_BASE_URL")
SIMAP_SEARCH_ENDPOINT = os.getenv("SIMAP_SEARCH_ENDPOINT")
SIMAP_DETAIL_ENDPOINT_TEMPLATE = os.getenv("SIMAP_DETAIL_ENDPOINT_TEMPLATE")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate configuration
required_env = [SIMAP_BASE_URL, SIMAP_SEARCH_ENDPOINT, SIMAP_DETAIL_ENDPOINT_TEMPLATE, SLACK_WEBHOOK_URL, OPENAI_API_KEY]
if not all(required_env):
    missing = [name for name, val in [
        ("SIMAP_BASE_URL", SIMAP_BASE_URL),
        ("SIMAP_SEARCH_ENDPOINT", SIMAP_SEARCH_ENDPOINT),
        ("SIMAP_DETAIL_ENDPOINT_TEMPLATE", SIMAP_DETAIL_ENDPOINT_TEMPLATE),
        ("SLACK_WEBHOOK_URL", SLACK_WEBHOOK_URL),
        ("OPENAI_API_KEY", OPENAI_API_KEY)
    ] if not val]
    raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# CPV filter codes (only these)
VALID_CPV_CODES = ["48000000", "72000000"]

company_profile = {
    "name": "Mesoneer GmbH",
    "domains": [
        "Identifikationssoftware",
        "Engineering (Workflow-Automation, RPA, Data Processing, Data-Plattform-Lösungen)",
        "AI & Data (Data Governance, Data Strategy, AI-Anwendungen)"
    ],
    "expertise": [
        "Process automatisation","Data Streaming","Data Plattforms",
        "Workflow Engines","IDP","RPA","Cloud","AI And GenAI",
        "Data Engineering","Data Governance and Strategy",
        "Identification Software","Kyc & Onboarding solutions"
    ],
    "technologies": ["BPMN 2.0", "Camunda BPM", "Axon Ivy", "Flowable", 
                     "Apache Kafka", "UiPath", "Microsoft Power Automate",
                     "Apache","Azure","Python","JAVA"],
    "max_contract_value_eur": 500_000
}

# OpenAI enrichment function schema
enrichment_functions = [
    {
        "name": "enrich_project",
        "description": (
            "Analysiere ein SIMAP-Projekt, fasse es kurz zusammen, "
            "extrahiere nur deutsche Werte, ordne es einem Team zu "
            "(Products, Engineering, Data&AI), gib einen Apply-Score 1–10 in wie fern wir geignet sind, "
            "und liste fehlende Felder als MissingInfo auf."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "project": {
                    "type": "object",
                    "properties": {
                        "title_de": {"type": "string"},
                        "customer": {"type": "string"},
                        "location": {"type": "string"},
                        "projectNumber": {"type": "string"},
                        "projectId":{"type": "string"},
                        "publicationDate": {"type": "string"},
                        "offerDeadline": {"type": "string"},
                        "contract_start": {"type": "string"},
                        "qna_deadline":{"type": "string"},
                        "cpvCode": {
                            "type": "object",
                            "properties": {
                                "code":     {"type": "string"},
                                "label_de": {"type": "string"}
                            },
                            "required": ["code","label_de"]
                        }
                    },
                    "required": [
                        "qna_deadline,title_de","customer","location","projectId"
                        "publicationDate","offerDeadline","contract_start","cpvCode","projectNumber"
                    ]
                },
                "team": {"type": "string", "enum": ["Products","Engineering","Data&AI"]},
                "apply_score": {
                    "type": "integer",
                    "description": "1–10, in wie fern sich eine Bewerbung lohnt auf Basis unserer Expertise,Technologien und Unternehmensprofil.",
                },
                "missing_info": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Welche relevanten Felder im JSON fehlten"
                }
            },
            "required": ["summary","project","team","apply_score","missing_info"]
        }
    }
]

# Helper: format ISO date to DD.MM.YYYY
def fmt_date(iso_str: str, fmt: str = "%d.%m.%Y") -> str:
    try:
        return datetime.fromisoformat(iso_str).strftime(fmt)
    except Exception:
        return iso_str or "—"

# Call SIMAP API endpoint and return JSON

def call_simap_api(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    url = f"{SIMAP_BASE_URL}{endpoint}"
    try:
        logger.debug(f"GET {url} params={params}")
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error(f"HTTP error {resp.status_code} calling {url}: {e}")
    except requests.RequestException as e:
        logger.error(f"Request error calling {url}: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from {url}: {e}")
    return None

# Fetch project summaries with pagination and CPV filter
def fetch_project_summaries(cpv, lang: str = "de", max_pages: int = 100) -> List[Dict[str, Any]]:
    summaries: List[Dict[str, Any]] = []
    cursor = None
    for page in range(max_pages):
        params = {"lang": lang, "processTypes": "open", "cpvCodes": cpv, "newestPublicationFrom": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")}
        if cursor:
            params["lastItem"] = cursor
        data = call_simap_api(SIMAP_SEARCH_ENDPOINT, params)
        if not data or "projects" not in data:
            break
        page_projects = data["projects"]
        summaries.extend(page_projects)
        pagination = data.get("pagination", {}) or {}
        cursor = pagination.get("lastItem")
        if not cursor or len(page_projects) < pagination.get("itemsPerPage", len(page_projects)):
            break
    logger.info(f"Fetched {len(summaries)} project summaries")
    return summaries

# Fetch detailed project JSONs for summaries
def fetch_project_details(summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    details: List[Dict[str, Any]] = []
    for ps in summaries:
        pid = ps.get("id")
        pubid = ps.get("publicationId")
        if not pid or not pubid:
            continue
        endpoint = SIMAP_DETAIL_ENDPOINT_TEMPLATE.format(projectId=pid, publicationId=pubid)
        data = call_simap_api(endpoint)
        if data:
            details.append(data)
        time.sleep(0.5)
    logger.info(f"Fetched details for {len(details)}/{len(summaries)} projects")

    projects_for_application = []
    if details:
        for project in details:
            pub_type = project.get("pubType", "").lower()
            if pub_type in ["tender", "advance_notice"]:
                projects_for_application.append(project)

    return projects_for_application

# Enrich a single project detail with OpenAI
def enrich_project(full_proj: dict, comp_profile: dict) -> dict:

    system_content = f"""
        Du bist RFP-Analyst für Mesoneer ag. Mesoneer ist Experte für:
        • Identifikationssoftware
        • Engineering (Automation, Data Processing, Plattformen)
        • AI & Data (Data Governance, Strategie, AI)

        Nutze nur die Felder aus dem SIMAP-JSON, die auf Deutsch vorliegen. Analysiere so:

        1. Schreibe eine kompakte Zusammenfassung (2–3 Sätze) in Deutsch.
        2. Extrahiere genau diese Felder aus dem JSON:
        • title_de, customer, location, publicationDate, offerDeadline, contract_start, cpvCode (code+label_de),qna_deadline,projectNumber,projectId
        3. Ordne das Projekt einem Team zu: Products, Engineering oder Data&AI.
        4. Vergib einen Apply-Score von 1–10, basierend auf:
        – Übereinstimmung mit unserem Profil (Domains, Expertise, Technologies)
        – Realistische Abschlusswahrscheinlichkeit:  
            • 1 = sehr unwahrscheinlich  
            • 10 = top-Potenzial  
        5. Liste in `missing_info` alle der sieben Felder auf, die im Input-JSON gar nicht zu finden waren.
        """
    resp = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content":
                "PROJECT_JSON =\n" + json.dumps(full_proj, ensure_ascii=False, indent=2)
                + "\n\nCOMPANY_PROFILE =\n" + json.dumps(comp_profile, ensure_ascii=False, indent=2)
            }
        ],
        functions=enrichment_functions,
        function_call={"name": "enrich_project"},
        temperature=0.2
    )
    func_call = resp.choices[0].message.function_call
    return json.loads(func_call.arguments)



def normalize(enriched: dict) -> dict:
    TARGET_KEYS = ["title_de","customer","location","publicationDate","offerDeadline","contract_start","cpvCode","qna_deadline","projectId"]
    proj = enriched["project"]
    for k in TARGET_KEYS:
        proj.setdefault(k, None)
    return enriched

# Post text to Slack webhook
def post_to_slack(text: str):
    resp = requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    resp.raise_for_status()

# Main execution pipeline
def main():
    summaries = fetch_project_summaries(cpv=VALID_CPV_CODES) # fetch yesterday's projects)
    details = fetch_project_details(summaries)
    for d in details:
        enriched = enrich_project(d)
        # Compose Slack text
        title = d.get("project-info", {}).get("title", {}).get("de") or d.get("project-info", {}).get("title", {}).get("fr", "–")
        score = enriched.get("apply_score")
        summary = enriched.get("summary")
        text = (
            "––––––––––––––––––––––––––––––––––––––––––––––––––\n"
            f":rocket: *Team:* {enriched.get('team')}    *# {d.get('projectNumber')}*\n"
            f":file_folder: *Projekt:* {title}\n"
            f":star: *Apply Score:* *{score}*\n\n"
            f":page_facing_up: *Zusammenfassung:*\n>{summary}\n\n"
            f":pushpin: *CPV:* `{(d.get('base') or {}).get('cpvCode', {}).get('code')}`\n"
            "––––––––––––––––––––––––––––––––––––––––––––––––––"
        )
        print(text)
        #post_to_slack(text)

if __name__ == "__main__":
    main()
