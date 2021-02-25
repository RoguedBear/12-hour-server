#!/usr/bin/env python3.8
# TODO: add tails -f log.log or less -R +F log.log in the readme
# TODO: add code style badge in README
import colorama
import requests
import logging
import subprocess
from colorama import Fore
from typing import Literal, Tuple

# program constants
CHAT_ID = ""
BOT_TOKEN = ""
SSID = ""
NIGHT_PHASE = None
MORNING_PHASE = None

# Logging formatter
FORMATTER = {
    "format": "{color}[{asctime}] :--{levelname:-^9s}--: [{funcName}()] {message}",
    # "format": "[%(asctime)s] | %(levelname)-6s | [%(funcName)s()]: %(message)s",
    "datefmt": "%d/%b/%Y %H:%M:%S",
    "colors": {
        "CRITICAL": Fore.RED,
        "INFO": Fore.WHITE,
        "ERROR": Fore.RED,
        "WARNING": Fore.YELLOW,
        "DEBUG": Fore.LIGHTWHITE_EX,
    },
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
    try:
        import yaml
        with open("config.yaml") as config_file:
            config = yaml.safe_load(config_file)
    except ModuleNotFoundError:
        logger.exception("pyyaml module nto found!\nare you sure you have installed requirements.txt")
        quit(1)
    except FileNotFoundError:
        logger.exception("config.yaml file not made. Please make it according to the specifications")
        quit(1)

    global SSID, NIGHT_PHASE, MORNING_PHASE, CHAT_ID, BOT_TOKEN
    # try and load each of the important stuff
    # Wifi
    try:
        SSID = config["ssid"]
    except KeyError:
        # logger.exception("SSID value not provided in config file!")
        # quit(1)
        logger.info("SSID not provided. Moving on...")
    else:
        logger.info(f'WiFi SSID "{SSID}" loaded...')

    # night phase timing
    try:
        NIGHT_PHASE = config["night phase"]
        assert "start time" in NIGHT_PHASE, "`start time` value missing in config file"
        assert "end time" in NIGHT_PHASE, "`end time` value missing in config file"
    except KeyError:
        logger.exception("`night phase` value not provided in config file!")
        quit(1)
    except AssertionError:
        logger.exception("Values for `night phase` are missing in config file!")
        quit(1)
    else:
        logger.info(f"Night Phase and it's timings loaded...")

    # morning phase timing
    try:
        MORNING_PHASE = config["morning phase"]
        assert (
            "start time" in MORNING_PHASE
        ), "`start time` value missing in config file"
        assert "end time" in MORNING_PHASE, "`end time` value missing in config file"
    except KeyError:
        logger.exception("`morning phase` value not provided in config file!")
        quit(1)
    except AssertionError:
        logger.exception("Values for `morning phase` are missing in config file!")
        quit(1)
    else:
        logger.info(f"Morning Phase and it's timings loaded...")

    # try loading Telegram bot token
    try:
        telegram = config["telegram"]
        assert "BOT_TOKEN" in telegram, "BOT_Token key in `telegram` not provided!"
        assert "CHAT_ID" in telegram, "CHAT_ID in `telegram` not provided!"
    except KeyError:
        logger.info("Telegram tokens not found. Moving over...")
        quit(1)
    except AssertionError as e:
        logger.exception(e)
        quit(1)
    else:
        BOT_TOKEN = telegram["BOT_TOKEN"]
        CHAT_ID = telegram["CHAT_ID"]
        logger.info("Telegram bot_token and chat id loaded...")

    try:
        TIMEOUT = config["timeout"]
        assert (
            isinstance(TIMEOUT, int) is True
        ), f"TIMEOUT not of correct type.\n Expected type int, got {type(TIMEOUT)}"
    except KeyError:
        logger.debug("timeout key not found. will use default")
    except AssertionError as e:
        logger.exception(e)
        quit(1)
    else:
        logger.info(f"Custom TIMEOUT({TIMEOUT} seconds) loaded...")


def alert_onTelegram(message: str):
    """
    This function will send an alert to telegram notifying about the change
    If BOT_TOKEN is not provided, this function will not run
    :param message: The message
    :return: None
    """
    if BOT_TOKEN and CHAT_ID:
        requests.get(
            "https://api.telegram.org/bot"
            + BOT_TOKEN
            + "/sendMessage?chat_id="
            + CHAT_ID
            + "&parse_mode=Markdown"
            "&text=" + message[:1000]
        )


# Initialise colorama
colorama.init(autoreset=True)

# Starting program logger

logger = logging.getLogger(__name__)

# Color logs on screen
colors = ColoredFormatter(FORMATTER["format"], datefmt=FORMATTER["datefmt"], style="{")
console = logging.StreamHandler()
console.setFormatter(colors)

# File logs uncolored
file_logs_uncolored = logging.FileHandler("logs.log")
uncolored_formatter = logging.Formatter(
    FORMATTER["format"].replace("{color}", ""), datefmt=FORMATTER["datefmt"], style="{"
)
file_logs_uncolored.setFormatter(uncolored_formatter)

# File logs colored
file_logs_colored = logging.FileHandler("logs_color.log")
file_logs_colored.setFormatter(colors)

# Adding those handlers
logger.addHandler(console)
logger.addHandler(file_logs_colored)
logger.addHandler(file_logs_uncolored)

logger.setLevel(10)

"""
ooooo   ooooo           oooo                                                                
`888'   `888'           `888                                                                
 888     888   .ooooo.   888  oo.ooooo.   .ooooo.  oooo d8b                                 
 888ooooo888  d88' `88b  888   888' `88b d88' `88b `888""8P                                 
 888     888  888ooo888  888   888   888 888ooo888  888                                     
 888     888  888    .o  888   888   888 888    .o  888                                     
o888o   o888o `Y8bod8P' o888o  888bod8P' `Y8bod8P' d888b                                    
                               888                                                          
                              o888o                                                         
                                                                                            
oooooooooooo                                       .    o8o                                 
`888'     `8                                     .o8    `"'                                 
 888         oooo  oooo  ooo. .oo.    .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.    .oooo.o 
 888oooo8    `888  `888  `888P"Y88b  d88' `"Y8   888   `888  d88' `88b `888P"Y88b  d88(  "8 
 888    "     888   888   888   888  888         888    888  888   888  888   888  `"Y88b.  
 888          888   888   888   888  888   .o8   888 .  888  888   888  888   888  o.  )88b 
o888o         `V88V"V8P' o888o o888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o 8""888P'
"""


def connected_to_wifi(ssid: str) -> bool:
    """
    checks whether the device is connected to wifi using linux's nmcli command.
    Assumes, that the device automatically connects to `ssid` if `ssid` is in range.
    so we just need to check if wifi scan discovers the ssid
    :param ssid: str, the name of the wifi network
    :return: bool
    """
    scan_output = subprocess.check_output(["nmcli", "device", "wifi", "list"]).decode()
    return ssid in scan_output


def check_connected_to_internetV2(
    connection_type: Literal["any", "wired", "wireless"] = "any"
) -> Tuple[bool, Tuple[str]]:
    """
    check's internet connectivity based on system's reporting.
    src: https://sourcedigit.com/20684-how-to-check-eth0-status-on-linux-ubuntu-find-network-interface-card-details-on-ubuntu/
    :param connection_type: the type of connection to check whether connected to internet or not. by default scans for ethernet and for wifi
    accepted arguments: 'wired', 'wireless', 'any'
    :return: bool
    """

    def get_card_status(card_name: str) -> int:
        """

        :param card_name: the name of the network card
        :return: int, 0 or 1
        """

        return int(
            subprocess.check_output(["cat", f"/sys/class/net/{card_name}/carrier"])
            .decode()
            .strip("\n")
        )

    network_devices = subprocess.check_output(["ls", "/sys/class/net"]).decode().split()
    wired = [e for e in network_devices if e[0] == "e"]
    wireless = [w for w in network_devices if w[0] == "w"]

    logger.debug(f"wired devices found ({len(wired)}): {wired}")
    logger.debug(f"wireless devices found ({len(wireless)}): {wireless}")
    CONNECTED_TO_INTERNET = False
    DEVICE_CONNECTED = []

    devices = {"wired": wired, "wireless": wireless, "any": wired + wireless}

    for card in devices[connection_type]:
        logger.debug("Testing device... " + Fore.CYAN + card)
        if get_card_status(card) == 1:
            CONNECTED_TO_INTERNET = True
            DEVICE_CONNECTED.append(card)
            logger.debug(
                f"Device: {Fore.CYAN + card + Fore.WHITE} is connected to internet"
            )

    return CONNECTED_TO_INTERNET, tuple(DEVICE_CONNECTED)


if __name__ == "__main__":
    config_loader()
    logger.debug(check_connected_to_internetV2())
