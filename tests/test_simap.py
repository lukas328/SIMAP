import os
import json
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from types import SimpleNamespace
import importlib

# Ensure required env vars for config
os.environ.setdefault("SLACK_WEBHOOK_URL", "http://example.com")
os.environ.setdefault("OPENAI_API_KEY", "dummy")

import simap_agent.config as config
importlib.reload(config)

import simap_agent.slack_client as slack_client
import simap_agent.simap_client as simap_client
import simap_agent.enricher as enricher


def test_format_slack_blocks_basic():
    proj = {
        "team": "Engineering",
        "project": {
            "title_de": "Projekt",
            "customer": "Kunde",
            "projectNumber": "123",
            "projectId": "abc",
            "offerDeadline": "2024-12-31",
            "contract_start": "2025-01-15",
            "qna_deadline": "2024-12-01",
            "cpvCode": {"code": "48000000", "label_de": "Software"},
        },
        "apply_score": 7,
        "summary": "Kurzfassung",
        "missing_info": [],
    }
    blocks = slack_client.format_slack_blocks(proj)
    assert any(b.get("type") == "section" for b in blocks)
    assert any(b.get("type") == "context" for b in blocks)
    section_text = next(b for b in blocks if b.get("type") == "section")["text"]["text"]
    assert "Projekt" in section_text
    assert "Engineering" in section_text


def test_enrich_missing_info(monkeypatch):
    detail = {"id": "1"}
    profile = {}

    fake_resp = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    function_call=SimpleNamespace(
                        arguments=json.dumps(
                            {
                                "summary": "s",
                                "project": {
                                    "title_de": "T",
                                    "customer": "C",
                                    "location": "L",
                                    "projectNumber": "PN",
                                    "projectId": None,
                                    "publicationDate": "2024-01-01",
                                    "offerDeadline": "2024-01-10",
                                    "contract_start": "2024-02-01",
                                    "qna_deadline": None,
                                    "cpvCode": {"code": "48000000", "label_de": "SW"},
                                },
                                "team": "Engineering",
                                "apply_score": 5,
                                "missing_info": [],
                            }
                        )
                    )
                )
            )
        ]
    )

    monkeypatch.setattr(
        enricher.openai_client.chat.completions,
        "create",
        lambda **kwargs: fake_resp,
    )
    monkeypatch.setattr(enricher, "summarize_criteria", lambda crit, name: "")

    result = enricher.enrich(detail, profile)
    assert sorted(result["missing_info"]) == [
        "Eignungskriterien",
        "ID",
        "Q&A",
        "Zuschlagskriterien",
    ]


def test_fetch_project_summaries_pagination(monkeypatch):
    pages = [
        {
            "projects": [{"id": "1"}],
            "pagination": {"lastItem": "cursor1", "itemsPerPage": 1},
        },
        {
            "projects": [{"id": "2"}],
            "pagination": {"lastItem": None, "itemsPerPage": 1},
        },
    ]
    calls = []

    def fake_call(endpoint, params=None):
        calls.append((endpoint, params))
        return pages.pop(0) if pages else None

    monkeypatch.setattr(simap_client, "call", fake_call)

    result = simap_client.fetch_project_summaries(["48000000"], max_pages=3)
    assert len(result) == 2
    assert len(calls) == 2


def test_fetch_project_details_filters(monkeypatch):
    summaries = [
        {"pubType": "tender", "id": "1", "publicationId": "p1"},
        {"pubType": "notice", "id": "2", "publicationId": "p2"},
        {"pubType": "advance_notice", "id": "3", "publicationId": "p3"},
    ]
    called = []

    def fake_call(endpoint, params=None):
        called.append(endpoint)
        return {"endpoint": endpoint}

    monkeypatch.setattr(simap_client, "call", fake_call)

    result = simap_client.fetch_project_details(summaries)
    assert len(result) == 2
    exp1 = simap_client.config.SIMAP_DETAIL_ENDPOINT_TEMPLATE.format(
        projectId="1", publicationId="p1"
    )
    exp2 = simap_client.config.SIMAP_DETAIL_ENDPOINT_TEMPLATE.format(
        projectId="3", publicationId="p3"
    )
    assert called == [exp1, exp2]
    assert result == [{"endpoint": exp1}, {"endpoint": exp2}]

