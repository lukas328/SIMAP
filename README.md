# SIMAP Agent

This tool fetches project tenders from [SIMAP](https://simap.ch), enriches them via OpenAI and posts the results to Slack.

## Installation
```bash
pip install -r requirements.txt
```

## Configuration
Create a `.env` file (see `.gitignore`) with the following variables:

- `SLACK_WEBHOOK_URL` – Slack Incoming Webhook
- `OPENAI_API_KEY` – OpenAI API key
- Optional: `SIMAP_BASE_URL`, `SIMAP_SEARCH_ENDPOINT`, `SIMAP_DETAIL_ENDPOINT_TEMPLATE`, `COMPANY_PROFILE_FILE`, `CPV_CODES`

## Usage
```bash
python -m simap_agent
```
The script will fetch recent projects, enrich them using OpenAI and post formatted messages to Slack. Enriched data is also written to `enriched_projects.json`.
