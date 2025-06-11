"""Azure Functions timer entry point for running the SIMAP agent."""

import logging
import azure.functions as func
from simap_agent.main import main as simap_main

def main(mytimer: func.TimerRequest) -> None:
    """Timer trigger that executes the SIMAP pipeline."""
    logging.info("SIMAP timer trigger executed")
    try:
        simap_main()
    except Exception:
        logging.exception("SIMAP timer failed")
        raise
