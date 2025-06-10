import json
import logging
import os
import sys

# Ensure package imports work when executed directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from simap_agent import config
from simap_agent.simap_client import fetch_project_summaries, fetch_project_details
from simap_agent.enricher import enrich_batch
from simap_agent.slack_client import format_slack_blocks, post_blocks

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
)
logger = logging.getLogger(__name__)

COMPANY_PROFILE = config.COMPANY_PROFILE
VALID_CPV = config.CPV_CODES


def main() -> None:
    logger.info("Starting SIMAP pipeline")
    logger.debug("Slack webhook configured: %s", bool(config.SLACK_WEBHOOK_URL))

    summaries = fetch_project_summaries(cpv=VALID_CPV)
    logger.debug("Fetched %d summaries", len(summaries))

    details = fetch_project_details(summaries)
    logger.debug("Fetched %d project details", len(details))

    logger.info("Enriching projects via OpenAI")
    enriched = enrich_batch(details, COMPANY_PROFILE)
    for det, enrich_data in zip(details, enriched):
        logger.info("Posting project #%s to Slack", det.get("projectNumber"))
        blocks = format_slack_blocks(enrich_data)
        logger.debug("Slack blocks: %s", blocks)
        try:
            post_blocks(blocks)
            logger.info("Slack post succeeded")
        except Exception:
            logger.exception("Failed to post message to Slack")

    logger.info("Writing enriched data to enriched_projects.json")
    with open("enriched_projects.json", "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    logger.info("Run completed")


if __name__ == "__main__":
    main()
