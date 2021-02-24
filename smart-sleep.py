#!/usr/bin/env python3
import colorama
import requests
import logging
from colorama import Fore

# program constants
CHAT_ID = ''
BOT_TOKEN = ''
SSID = ''
NIGHT_PHASE = None
MORNING_PHASE = None

# Logging formatter
FORMATTER = {
    "format": "{color}[{asctime}] -- {levelname:>6s} -- {message}",
    # "format": "[%(asctime)s] | %(levelname)-6s | [%(funcName)s()]: %(message)s",
    "datefmt": "%d/%b/%Y %H:%M:%S",
    "colors": {
        "CRITICAL": Fore.RED,
        "INFO": Fore.WHITE,
        "ERROR": Fore.RED,
        "WARNING": Fore.YELLOW,
        "DEBUG": Fore.LIGHTWHITE_EX
    }
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, datefmt=None, style=None):
        logging.Formatter.__init__(self, msg, datefmt, style)

    def format(self, record):
        if record.levelname in FORMATTER["colors"]:
            record.color = FORMATTER["colors"][str(record.levelname)]

        return logging.Formatter.format(self, record)



def config_loader(filename: str = "config.yaml") -> dict:
    """
    Loads the config from the `filename` and returns the dictionary from it and sets the program constants
    :param filename: str, the filename
    :return: dictionary
    """
    import yaml
    with open('config.yaml') as config_file:
        config = yaml.safe_load(config_file)

    global SSID, NIGHT_PHASE, MORNING_PHASE
    try:
        SSID = config['ssid']
    except KeyError:
        logger.exception("SSID value not provided in config file!")


def alert_onTelegram(message: str):
    """
    This function will send an alert to telegram notifying about the change
    If BOT_TOKEN is not provided, this function will not run
    :param message: The message
    :return: None
    """
    if BOT_TOKEN and CHAT_ID:
        requests.get(
            "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage?chat_id=" + CHAT_ID + "&parse_mode=Markdown"
                                                                                             "&text=" + message[:1000])


# Initialise colorama
colorama.init(autoreset=True)

# Starting program logger

logger = logging.getLogger(__name__)
console = logging.StreamHandler()
colors = ColoredFormatter(FORMATTER['format'], datefmt=FORMATTER['datefmt'], style="{")
console.setFormatter(colors)
logger.addHandler(console)
logger.setLevel(10)
if __name__ == '__main__':
    logger.info("hello")
    config_loader()
