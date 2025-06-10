# SIMAP Agent

Dieses Projekt automatisiert das Abrufen und Aufbereiten von Ausschreibungen aus [SIMAP](https://simap.ch). Die Daten werden mit Hilfe von OpenAI angereichert und anschliessend als formatierte Nachrichten an Slack gesendet.

## Installation
```bash
pip install -r requirements.txt
```

## Konfiguration
`.env`-Datei beinhaltet folgende Variablen :

- `SLACK_WEBHOOK_URL` – URL des Slack Incoming Webhooks
- `OPENAI_API_KEY` – API-Schlüssel für OpenAI
- Optional: `SIMAP_BASE_URL`, `SIMAP_SEARCH_ENDPOINT`, `SIMAP_DETAIL_ENDPOINT_TEMPLATE`, `COMPANY_PROFILE_FILE`, `CPV_CODES`

## Nutzung
```bash
python -m simap_agent
```
Das Skript ruft aktuelle Projekte ab, nutzt OpenAI zur Anreicherung und postet die Ergebnisse in Slack. Die angereicherten Daten werden ebenfalls in `enriched_projects.json` geschrieben.

## Deployment
Das Projekt läuft in einer Azure Function, die nach einem täglich um 7:00 nach einen festen Zeitplan ausgeführt wird:

```
<AZURE_FUNCTION_APP_NAME_PLACEHOLDER>
```

Die Umgebungsvariablen sind ebenfalls in Azure Function konfiguriert.
