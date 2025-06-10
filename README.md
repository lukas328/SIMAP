# SIMAP Agent

Dieses Projekt automatisiert das Abrufen und Aufbereiten von Ausschreibungen aus [SIMAP](https://simap.ch). Die Daten werden mit Hilfe von OpenAI angereichert und anschliessend als formatierte Nachrichten an Slack gesendet.

## Installation
```bash
pip install -r requirements.txt
```

## Konfiguration
Legen Sie eine `.env`-Datei an (siehe `.gitignore`) und fügen Sie folgende Variablen ein:

- `SLACK_WEBHOOK_URL` – URL des Slack Incoming Webhooks
- `OPENAI_API_KEY` – API-Schlüssel für OpenAI
- Optional: `SIMAP_BASE_URL`, `SIMAP_SEARCH_ENDPOINT`, `SIMAP_DETAIL_ENDPOINT_TEMPLATE`, `COMPANY_PROFILE_FILE`, `CPV_CODES`

## Nutzung
```bash
python -m simap_agent
```
Das Skript ruft aktuelle Projekte ab, nutzt OpenAI zur Anreicherung und postet die Ergebnisse in Slack. Die angereicherten Daten werden ebenfalls in `enriched_projects.json` geschrieben.

## Deployment
Das Projekt läuft in einer Azure Function, die nach einem festen Zeitplan ausgeführt wird. Die genaue Umgebung und der Name der Function App werden intern gepflegt und müssen hier eingetragen werden:

```
<AZURE_FUNCTION_APP_NAME_PLACEHOLDER>
```

Bitte stellen Sie sicher, dass die Umgebungsvariablen auch in der Azure Function konfiguriert sind.
