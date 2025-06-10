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
- Optional: `SIMAP_BASE_URL`, `SIMAP_SEARCH_ENDPOINT`, `SIMAP_DETAIL_ENDPOINT_TEMPLATE`, `COMPANY_PROFILE_FILE`, `CPV_CODES`, `APPLY_SCORE_THRESHOLD`

## Usage
```bash
python -m simap_agent
```
The script will fetch recent projects, enrich them using OpenAI and post formatted messages to Slack. Enriched data is also written to `enriched_projects.json`.

## Azure Functions
The repository includes a simple timer-triggered Azure Function under `azure_function/simap_timer`.
To deploy:
1. Install the [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local) and the Azure CLI.
2. Run `func azure functionapp publish <APP_NAME>` from the repository root to deploy.
3. Configure the required environment variables (`SLACK_WEBHOOK_URL`, `OPENAI_API_KEY`, ...)
   in the Function App settings.
The schedule can be adjusted in `azure_function/simap_timer/function.json`.
