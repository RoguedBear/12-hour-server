#!/usr/bin/env python3.8
# TODO: add tails -f log.log or less -R +F log.log in the readme
# TODO: add code style badge in README
import datetime
from time import sleep

import colorama
import requests
import logging
import subprocess
from colorama import Fore
from typing import Literal, Tuple, Dict, Optional

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
    """
888                        888                                 .d888 
888                        888                                d88P"  
888                        888                                888    
888  .d88b.   8888b.   .d88888       .d8888b .d88b.  88888b.  888888 
888 d88""88b     "88b d88" 888      d88P"   d88""88b 888 "88b 888    
888 888  888 .d888888 888  888      888     888  888 888  888 888    
888 Y88..88P 888  888 Y88b 888      Y88b.   Y88..88P 888  888 888    
888  "Y88P"  "Y888888  "Y88888       "Y8888P "Y88P"  888  888 888    
                                                                     
                                                                     
                                                                     
    """
    try:
        import yaml

        with open(filename) as config_file:
            config = yaml.safe_load(config_file)
    except ModuleNotFoundError:
        logger.exception(
            "pyyaml module nto found!\nare you sure you have installed requirements.txt"
        )
        quit(1)
    except FileNotFoundError:
        logger.exception(
            "config.yaml file not made. Please make it according to the specifications"
        )
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
        NIGHT_PHASE["name"] = "NIGHT PHASE"

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
        MORNING_PHASE["name"] = "MORNING PHASE"

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

    """
8888888b.                                         88888888888 d8b                        
888   Y88b                                            888     Y8P                        
888    888                                            888                                
888   d88P 8888b.  888d888 .d8888b   .d88b.           888     888 88888b.d88b.   .d88b.  
8888888P"     "88b 888P"   88K      d8P  Y8b          888     888 888 "888 "88b d8P  Y8b 
888       .d888888 888     "Y8888b. 88888888          888     888 888  888  888 88888888 
888       888  888 888          X88 Y8b.              888     888 888  888  888 Y8b.     
888       "Y888888 888      88888P'  "Y8888           888     888 888  888  888  "Y8888                                                                                           
    """

    # Parsing Night Phase + Morning Phase timings

    for phase in [NIGHT_PHASE, MORNING_PHASE]:
        try:
            times = parse_time(phase)
        except AssertionError as e:
            logger.error(
                "Datetime value in config.yml for '%s' not in range\nValueError:%s",
                phase["name"].lower(),
                e,
            )
            quit(1)
        except TypeError as e:
            logger.error(
                "Datetime value in config.yml for '%s' not in right format\nTypeError:%s",
                phase["name"].lower(),
                e,
            )
            quit(1)
        else:
            phase["start time"] = times["start time"]
            phase["end time"] = times["end time"]
            logger.info("Parsing time for %s... %sDone", phase["name"], Fore.GREEN)
            logger.info(
                "Time range loaded for %s: (%s — %s)",
                phase["name"],
                str(phase["start time"]),
                str(phase["end time"]),
            )
    return config


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


"""
888                            d8b                   
888                            Y8P                   
888                                                  
888  .d88b.   .d88b.   .d88b.  888 88888b.   .d88b.  
888 d88""88b d88P"88b d88P"88b 888 888 "88b d88P"88b 
888 888  888 888  888 888  888 888 888  888 888  888 
888 Y88..88P Y88b 888 Y88b 888 888 888  888 Y88b 888 
888  "Y88P"   "Y88888  "Y88888 888 888  888  "Y88888 
                  888      888                   888 
             Y8b d88P Y8b d88P              Y8b d88P 
              "Y88P"   "Y88P"                "Y88P"  
"""

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


def parse_time(phase_dict: dict) -> Dict[str, datetime.timedelta]:
    """
    Returns the new dictionary with parsed datetime from string
    :param phase_dict: the phase dictionary containing datetime string
    :return:
    """
    logger.debug("Data received: %s", phase_dict)
    ultimate_time = datetime.timedelta(hours=23, minutes=59, seconds=59)
    start_time = phase_dict["start time"]
    end_time = phase_dict["end time"]
    converted_time = []
    for index, time in enumerate([start_time, end_time]):
        time_key = "start time" if index == 0 else "end time"
        try:
            # now we convert those "seconds" to "hours". aka instead of 1600 hrs -> 16min -> 960s to 1600hrs -> 57600
            time = datetime.timedelta(seconds=time * 60)
        except TypeError as e:
            raise TypeError(str(e) + " [\"{}\" in '{}']".format(time, time_key))
        else:
            assert datetime.timedelta(seconds=0) <= time <= ultimate_time, (
                f"'{time_key}' value '{phase_dict[time_key] // 60}:{phase_dict[time_key] % 60}' out of range! Ensure "
                f"the "
                "time is in 24hr format and lies between 00:00 <= time <= 23:59:59"
            )
            converted_time.append(time)
    # breakpoint()

    return {"start time": converted_time[0], "end time": converted_time[1]}


def get_current_time_delta() -> datetime.timedelta:
    """
    returns the current time in timedelta format
    :return:
    """
    current_time = datetime.datetime.now()
    return datetime.timedelta(
        hours=current_time.hour,
        minutes=current_time.minute,
        seconds=current_time.second,
    )


def current_time_within_time_range(phase: dict) -> bool:
    """
    checks whether the current time is within the start-time <= time < end-time range
    :param phase: dictionary containing the phase's start and end time
    :return: bool
    """
    return phase["start time"] <= get_current_time_delta() < phase["end time"]


def get_nearest_phase(
    *args, key: Literal["start time", "end time"] = "start time"
) -> Tuple[str, datetime.timedelta]:
    """
    This function will return the phase which is nearest to the current time.
    We'll get a list/tuple of all the phase names and their start timings.
    Then run the super complex python expression to get the nearest phase
    :param key: the key to check within range against
    :param args:
    :return: tuple of the nearest phase and the time left until then
    """
    now = get_current_time_delta()

    def key_function(dict_):
        """
        This function will be the "key" function to be put in max()'s key arg
        :param dict_: the dict
        :return: the output of the difference b/w current time and the start time of the phase
        """
        return dict_[key] - now

    logger.debug("%s\t%s", args, list(map(key_function, args)))
    answer = max(args, key=key_function)
    return answer["name"], answer["start time"] - now


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
    src: https://sourcedigit.com/20684-how-to-check-eth0-status-on-linux-ubuntu-find-network-interface-card-details-on-
    ubuntu/
    :param connection_type: the type of connection to check whether connected to internet or not. by default scans for
    ethernet and for wifi
    accepted arguments: 'wired', 'wireless', 'any'
    :return: bool
    """

    def get_card_status(card_name: str) -> int:
        """
        checks and returns the status of network cards [wired and/or wireless] and if they're connected to internet
        or not as reported by the system
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


def sleep_computer_but_wake_at(time: datetime.timedelta, debug: bool = False):
    """
    sleeps the computer when func is executed and sets the wake timer till `time` seconds using rtcwake
    Assumes the time is greater than `now` time.
    :param time: the datetime.timedelta object of the time you need the computer to wake up at
    :return: None
    Raises a ValueError if time is less than current time
    """
    # get the time in seconds left until wake time
    time_to_wake_up = time - get_current_time_delta()

    # check if time isn't negative
    if time_to_wake_up.total_seconds() <= 0:
        raise ValueError("Given time passed in as argument has already passed!")

    # now we go schleep schleep
    wake_up_print = datetime.datetime.combine(
        datetime.datetime.today().date(), (datetime.datetime.min + time).time()
    )
    wake_up_print = wake_up_print.strftime("%d/%b/%Y %H:%M:%S")
    logger.info("Going schleep schleep, and will wake up at %s.", wake_up_print)
    if not debug:
        output = subprocess.check_output(
            ["sudo", "rtcwake", "-m", "mem", "-s", str(time_to_wake_up.seconds)]
        )
    else:
        output = subprocess.check_output(
            ["sudo", "rtcwake", "-m", "on", "-s", str(time_to_wake_up.seconds)]
        )
    logger.debug(output.decode())
    logger.info('"Good Mawrning!" [read that in Tim Cook way] I am awake now.')


def suspend_thread_until(time: datetime.timedelta):
    """
    suspends the current thread until the `time` time reaches using time.sleep()
    :param time: the time to wake the thread
    :return: None
    """
    time_to_wake_up = time - get_current_time_delta()
    sleep(time_to_wake_up.total_seconds())


def sleep_or_suspend_until(time: datetime.timedelta, mode: Literal["suspend", "sleep"]):
    """
    This function will take the time, and choice of the user to either: sleep the computer, or suspend the thread. aka
    time.sleep() suspend.
    Will also pause the program for a few seconds to give the computer time to connect to the wifi.
    :param time: time to wake the computer/thread at
    :param mode:
        - 'suspend': will time.sleep() the thread.
        - 'sleep': will make the computer go to sleep.
    :return:
    """
    if mode == 'suspend':
        suspend_thread_until(time)
    elif mode == 'sleep':
        sleep_computer_but_wake_at(time, debug=True)
    else:
        logger.error("'%s' is not a valid argument for parameter 'mode'. 'mode' can either be 'sleep' or 'suspend'",
                     mode)
    logger.debug("%s is awake now, suspending the thread for 5 seconds...", 'computer' if mode == 'sleep' else 'program')
    sleep(5)


"""
                888b     d888        d8888 8888888 888b    888 
                8888b   d8888       d88888   888   8888b   888 
                88888b.d88888      d88P888   888   88888b  888 
                888Y88888P888     d88P 888   888   888Y88b 888 
                888 Y888P 888    d88P  888   888   888 Y88b888 
                888  Y8P  888   d88P   888   888   888  Y88888 
                888   "   888  d8888888888   888   888   Y8888 
                888       888 d88P     888 8888888 888    Y888 
"""

if __name__ == "__main__":
    debug = True
    if debug:
        config_loader()
        logger.debug("Testing check_connected_to_internetV2() function:")
        logger.debug("Result:" + Fore.CYAN + str(check_connected_to_internetV2()))

        # test sleep function
        delta = get_current_time_delta() + datetime.timedelta(seconds=10)
        # sleep_computer_but_wake_at(delta, debug=True)

        print(get_nearest_phase(MORNING_PHASE, NIGHT_PHASE))

    # The main big brain logic of the program
    """Pseudocode:
    *check which phase is the nearest to us.
    *check if we are in the night phase or morning phase.
    -NIGHT PHASE
    * check if internet is still connected
    * if yes. no problem. check again in TIMEOUT seconds.
    * if internet is not there, wait 5-10 minute (or WIFI_Wait).
        * if internet still not there, sleep until morning phase
    * if we're within ~TIMEOUT seconds of `end time` of the NIGHT PHASE, go to sleep
    
    - MORNING PHASE
    * wakey wakey and see if internet is connected. after waiting 60 seconds giving the computer oppurtunity to connect
    * if internet not there, sleep and check again in TIMEOUT seconds
    * if internet there no problem. awake, sleep until NighPhase
    * if we're within ~TIMEOUT seconds of `end time` of morning phase, we'll go awake and sleep the thread until 
       NIGHTPHASE arrives
    
    - NEITHER
    * if we're in neither phase (possibly cuz you ran the program at your own will), suspend the thread if nearest is 
      NIGHT, else sleep if the nearest is morning
    """
