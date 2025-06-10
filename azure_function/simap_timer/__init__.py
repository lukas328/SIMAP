import logging
import azure.functions as func
from simap_agent.main import main as simap_main

def main(mytimer: func.TimerRequest) -> None:
    logging.info("SIMAP timer trigger executed")
    simap_main()
