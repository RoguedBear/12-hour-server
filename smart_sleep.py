#!/usr/bin/sudo python3.8
# TODO: add tails -f log.log or less -R +F log.log in the readme
# TODO: add code style badge in README
import datetime
from time import sleep

import colorama
import requests
import logging
import subprocess
from colorama import Fore
from typing import Literal, Tuple, Dict

# program constants
CHAT_ID = ""
BOT_TOKEN = ""
CONNECTION_TYPE: Literal["any", "wired", "wireless"] = "any"
NIGHT_PHASE: dict = dict()
MORNING_PHASE: dict = dict()
TIMEOUT = 500
SLEEP_INTERVAL = 0  # 0 means disabled

# This controls whether the computer sleeps for real or not. change it acc to your needs
DEBUG = False
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

    global CONNECTION_TYPE, NIGHT_PHASE, MORNING_PHASE, CHAT_ID, BOT_TOKEN, TIMEOUT, SLEEP_INTERVAL
    # try and load each of the important stuff
    # Wifi
    try:
        CONNECTION_TYPE = config["connection type"]
    except KeyError:
        logger.exception("CONNECTION_TYPE value not provided in config file!")
        quit(1)
        # logger.info("CONNECTION_TYPE not provided. Moving on...")
    else:
        logger.info(f'CONNECTION_TYPE: "{CONNECTION_TYPE}" loaded...')

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

    # load sleep_interval
    try:
        SLEEP_INTERVAL = config["sleep_interval"]
        assert isinstance(
            SLEEP_INTERVAL, (int, float)
        ), "sleep_interval is not an integer"
    except KeyError:
        logger.debug("no sleep_interval defined")
    except AssertionError as e:
        logger.exception(e)
        quit(1)
    else:
        logger.info(f"Loaded sleep interval of: {SLEEP_INTERVAL} seconds")

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
        x = requests.get(
            "https://api.telegram.org/bot"
            + BOT_TOKEN
            + "/sendMessage?chat_id="
            + str(CHAT_ID)
            + "&parse_mode=Markdown"
            "&text=" + message[:1000]
        )
        logger.debug(x)


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
            try:
                time = datetime.datetime.strptime(time, "%H:%M")
                time = datetime.timedelta(hours=time.hour, minutes=time.minute)
            except ValueError:
                raise TypeError(str(e) + " [\"{}\" in '{}']".format(time, time_key))

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
    # thank you https://stackoverflow.com/questions/30529437/python-time-comparison-at-midnight
    now = get_current_time_delta()
    logger.debug("Phase start time: %s\t Current time:%s", phase["start time"], now)
    if phase["start time"] <= phase["end time"]:
        return phase["start time"] <= now < phase["end time"]
    else:
        return phase["start time"] <= now or phase["end time"] > now
    # return phase["start time"] <= get_current_time_delta() < phase["end time"]


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

    logger.debug("%s\n\t%s", args, list(map(key_function, args)))
    answer = min(args, key=key_function)
    return answer["name"], answer["start time"] - now


def get_nearest_phaseV2(phase1, phase2) -> Tuple[str, datetime.timedelta]:
    """
    This function will return the phase which is nearest to the current time.
    :param phase1: the first phase time + name dict
    :param phase2: the second phase time + name dict
    :return: tuple of the nearest phase and the time left until then
    """
    now = get_current_time_delta()
    range_1 = {
        "name": phase2["name"],
        "start time": phase1["end time"],
        "end time": phase2["start time"],
    }
    range_2 = {
        "name": phase1["name"],
        "start time": phase2["end time"],
        "end time": phase1["start time"],
    }
    if current_time_within_time_range(range_1):
        return range_1["name"], range_1["start time"] - now
    elif current_time_within_time_range(range_2):
        return range_2["name"], range_2["start time"] - now


def repr_time_delta(time: datetime.timedelta):
    """
    represents the passed in time delta as a proper date
    :param time:
    :return:
    """
    formated_time = datetime.datetime.combine(
        datetime.datetime.today().date(), (datetime.datetime.min + time).time()
    )
    return formated_time.strftime("%d/%b/%Y %H:%M:%S")


def get_last_sleep_time() -> datetime.datetime:
    """
    returns tha last sleep time in datetime.datetime format.
    uses the command: grep -E "PM: suspend entry" /var/log/syslog
    to get the last sleep time from system logs
    Since the year is not present in log file, assumes the last sleep time is the current year
    :return: the last sleep time. datetime.datetime.min if unable to find the last sleep time.
    """
    try:
        sleep_entry_entries = subprocess.check_output(
            'grep -E "PM: suspend entry" /var/log/syslog; exit 0', shell=True
        ).decode()
        assert len(sleep_entry_entries) != 0, "No last sleep time recorded"
    except (subprocess.CalledProcessError, AssertionError):
        last_sleep_entry = datetime.datetime.min
    else:
        sleep_entry_entries = sleep_entry_entries.split("\n")[:-1]
        last_sleep_entry = sleep_entry_entries[-1].split()
        month_date_time = " ".join(last_sleep_entry[0:3])
        last_sleep_entry = datetime.datetime.strptime(month_date_time, "%b %d %H:%M:%S")
        last_sleep_entry.replace(year=datetime.date.today().year)
    return last_sleep_entry


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

        try:
            result = int(
                subprocess.check_output(["cat", f"/sys/class/net/{card_name}/carrier"])
                .decode()
                .strip("\n")
            )
        except subprocess.CalledProcessError:
            result = (
                subprocess.check_output(
                    ["cat", f"/sys/class/net/{card_name}/operstate"]
                )
                .decode()
                .strip("\n")
            )
            result = 1 if result == "up" else 0
        return result

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
    if not DEVICE_CONNECTED:
        logger.debug(
            "No device connected to internet. Computer is currently %sOFFLINE",
            Fore.YELLOW,
        )

    return CONNECTED_TO_INTERNET, tuple(DEVICE_CONNECTED)


# noinspection PyShadowingNames
def sleep_computer_but_wake_at(time: datetime.timedelta, debug: bool = False):
    """
    sleeps the computer when func is executed and sets the wake timer till `time` seconds using rtcwake
    Assumes the time is greater than `now` time.
    :param time: the datetime.timedelta object of the time you need the computer to wake up at
    :return: None
    :param debug: true to debug and not make the computer sleep but just display the waketimer in stdout
    Raises a ValueError if time is less than current time
    """
    # get the time in seconds left until wake time
    time_to_wake_up = time - get_current_time_delta()

    # # check if time isn't negative
    # if time_to_wake_up.total_seconds() <= 0:
    if time_to_wake_up < datetime.timedelta(seconds=0):
        time_to_wake_up += datetime.timedelta(hours=24)

    # now we go schleep schleep
    logger.info("Going schleep schleep, and will wake up at %s.", repr_time_delta(time))
    if not debug:
        output = subprocess.check_output(
            ["sudo", "rtcwake", "-m", "mem", "-s", str(time_to_wake_up.seconds)]
        )
    else:
        output = subprocess.check_output(
            ["sudo", "-s", "rtcwake", "-m", "on", "-s", str(time_to_wake_up.seconds)]
        )
    logger.debug(output.decode())
    sleep(2)
    logger.info('"Good Mawrning!" [read that in Tim Cook way] I am awake now.')


def suspend_thread_until(time: datetime.timedelta):
    """
    suspends the current thread until the `time` time reaches using time.sleep()
    :param time: the time to wake the thread
    :return: None
    """
    time_to_wake_up = time - get_current_time_delta()
    if time_to_wake_up < datetime.timedelta(seconds=0):
        time_to_wake_up += datetime.timedelta(hours=24)

    # time adjustments
    if SLEEP_INTERVAL:
        time_to_wake_up = min(
            time_to_wake_up, datetime.timedelta(seconds=SLEEP_INTERVAL)
        )
        time = get_current_time_delta() + time_to_wake_up

    logger.debug(
        "Sleeping the program until %s for duration %s...",
        repr_time_delta(time),
        str(time_to_wake_up),
    )
    # if there's no SLEEP_INTERVAL key aka 0
    if SLEEP_INTERVAL:
        output = subprocess.check_output(
            ["sudo", "-s", "rtcwake", "-m", "on", "-s", str(time_to_wake_up.seconds)]
        )
        logger.debug(output.decode())
    else:
        sleep(time_to_wake_up.total_seconds())
    # extra delay seconds
    sleep(1)


def sleep_or_suspend_until(time: int, mode: Literal["suspend", "sleep"]):
    """
    This function will take the time, and choice of the user to either: sleep the computer, or suspend the thread. aka
    time.sleep() suspend.
    Will also pause the program for a few seconds to give the computer time to connect to the wifi.
    :param time: the "duration" of seconds to wake the computer/thread after the "current" time
    :param mode:
        - 'suspend': will time.sleep() the thread.
        - 'sleep': will make the computer go to sleep.
    :return:
    """
    time = get_current_time_delta() + datetime.timedelta(seconds=time)
    if mode == "suspend":
        suspend_thread_until(time)
    elif mode == "sleep":
        sleep_computer_but_wake_at(time, debug=DEBUG)
    else:
        logger.error(
            "'%s' is not a valid argument for parameter 'mode'. 'mode' can either be 'sleep' or 'suspend'",
            mode,
        )
    DELAY = 5
    logger.debug(
        "%s is awake now, suspending the thread for %d more seconds...",
        "computer" if mode == "sleep" else "program",
        DELAY,
    )
    sleep(DELAY)


"""
                                                                                    
    88           88               88                                   88               
    88           ""               88                                   ""               
    88                            88                                                    
    88,dPPYba,   88   ,adPPYb,d8  88,dPPYba,   8b,dPPYba,  ,adPPYYba,  88  8b,dPPYba,   
    88P'    "8a  88  a8"    `Y88  88P'    "8a  88P'   "Y8  ""     `Y8  88  88P'   `"8a  
    88       d8  88  8b       88  88       d8  88          ,adPPPPP88  88  88       88  
    88b,   ,a8"  88  "8a,   ,d88  88b,   ,a8"  88          88,    ,88  88  88       88  
    8Y"Ybbd8"'   88   `"YbbdP"Y8  8Y"Ybbd8"'   88          `"8bbdP"Y8  88  88       88  
                      aa,    ,88                                                        
                       "Y8bbdP"                                                         
                                                                                        
                88                                    88                                            
                88                                    ""                                            
                88                                                                                  
                88           ,adPPYba,    ,adPPYb,d8  88   ,adPPYba,                                
                88          a8"     "8a  a8"    `Y88  88  a8"     ""                                
                88          8b       d8  8b       88  88  8b                                        
                88          "8a,   ,a8"  "8a,   ,d88  88  "8a,   ,aa                                
                88888888888  `"YbbdP"'    `"YbbdP"Y8  88   `"Ybbd8"'                                
                                          aa,    ,88                                                
                                           "Y8bbdP"                                                 
"""


def wait_for_connectivity_to_change_to(
    req_connection_status: Literal["connected", "disconnected"],
    action: Literal["suspend", "sleep"],
    start_time: datetime.timedelta,
    end_time: datetime.timedelta,
    timeout: int = -1,
) -> bool:
    """
    This function is partly big brain logic.
    It will take in two arguments. one to check what part to respond to. either disconnection from internet, or
    connection to internet
    the second argument will tell whether to suspend the thread or sleep the computer if status of connectivity remains
    same.
    This function will keep on running until the connectivity becomes what was specified. eg: if wait for
    connection, then function will continue until computer connects to internet
    if wait for disconnection, then program will continue until the connectivity drops
    If computer/server is connected to the internet, then function will run until the connection drops
    :param req_connection_status: the connection stage to wait
    :param action: sleep/suspend the computer/thread when waiting for TIMEOUT duration to check for connectivity changes
    :param start_time: the starting time of the current phase
    :param end_time: the time till the function should check for connection changes
    :param timeout: *Optional. -1 by default to use the default TIMEOUT. otherwise specify timeout
    :return: True/False if connection changed to what was asked
    """
    # convert connection types to a boolean dictionary
    con_val = {"connected": True, "disconnected": False}
    # We start with an infinite loop.
    logger.info("Waiting for connectivity to change to '%s'...", req_connection_status)
    # PRocess end_time to account for cur_time < 12am but end_time > 12am
    phase = {
        "start time": start_time,
        "end time": end_time,
    }
    while current_time_within_time_range(phase):
        # We check now the status of internet connection.
        status, _ = check_connected_to_internetV2(CONNECTION_TYPE)

        # Now check if the internet status is the same as required status' boolean value
        if status == con_val[req_connection_status]:
            old = "disconnected" if con_val[req_connection_status] else "connected"
            new = "connected" if status else "disconnected"
            logger.info("Connection status has been changed! (%s -> %s)", old, new)
            return True
        # If the internet status is not what is required, then we just wait for TIMEOUT duration and check back
        # again
        else:
            # refresh timeout
            timeout = TIMEOUT if timeout == -1 else timeout
            sleep_or_suspend_until(timeout, action)
            continue
    logger.info("Connectivity did not change in the specified time.")
    return False


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
    LAST_SLEEP_TIME = get_last_sleep_time()
    LAST_SLEEP_TIME_byProgram = datetime.datetime.min
    _wake_up_message_sent = False
    debug = False
    # if debug:
    #     config_loader()
    #     logger.debug("Testing check_connected_to_internetV2() function:")
    #     logger.debug("Result:" + Fore.CYAN + str(check_connected_to_internetV2()))
    #
    #     # test sleep function
    #     delta = get_current_time_delta() + datetime.timedelta(seconds=10)
    #     # sleep_computer_but_wake_at(delta, debug=True)
    #
    #     print(get_nearest_phaseV2(MORNING_PHASE, NIGHT_PHASE))
    #
    #     sleep_or_suspend_until(10, "suspend")

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
    config_data = config_loader()
    logging_level = config_data.get("logging level", 10)
    logger.setLevel(logging_level)
    # Alright, let's start.
    while True:
        go_to_sleep = False
        be_awake = False

        # Check if we're in NIGHT PHASE
        if current_time_within_time_range(NIGHT_PHASE):
            logger.info(f"Computer is in {Fore.LIGHTMAGENTA_EX} night phase")
            _wake_up_message_sent = False
            # In the night mode, check if we're nearing the end time, if yes then check *vigorously* for connectivity
            # changes
            if current_time_within_time_range(
                {
                    "start time": NIGHT_PHASE["end time"]
                    - datetime.timedelta(seconds=TIMEOUT),
                    "end time": NIGHT_PHASE["end time"],
                }
            ):
                go_to_sleep = wait_for_connectivity_to_change_to(
                    "disconnected",
                    "suspend",
                    NIGHT_PHASE["start time"],
                    NIGHT_PHASE["end time"],
                    60,
                )

            # Otherwise passively check for connectivity changes till
            else:
                go_to_sleep = wait_for_connectivity_to_change_to(
                    "disconnected",
                    "suspend",
                    NIGHT_PHASE["start time"],
                    NIGHT_PHASE["end time"] - datetime.timedelta(seconds=TIMEOUT),
                )

        # Check if we're in MORNING PHASE now
        elif current_time_within_time_range(MORNING_PHASE):
            logger.info(f"Computer is in {Fore.LIGHTMAGENTA_EX} morning phase.")
            # Check if we're nearing the end time. ig yes, then check vigorously

            if current_time_within_time_range(
                {
                    "start time": MORNING_PHASE["end time"]
                    - datetime.timedelta(seconds=TIMEOUT),
                    "end time": MORNING_PHASE["end time"],
                }
            ):
                be_awake = wait_for_connectivity_to_change_to(
                    "connected",
                    "suspend",
                    MORNING_PHASE["start time"],
                    MORNING_PHASE["end time"],
                    60,
                )
            else:
                be_awake = wait_for_connectivity_to_change_to(
                    "connected",
                    "sleep",
                    MORNING_PHASE["start time"],
                    MORNING_PHASE["end time"] - datetime.timedelta(seconds=TIMEOUT),
                )

        # here we see which phase is the nearest to us and take actions accordingly
        else:
            logger.info(f"Computer is in {Fore.LIGHTMAGENTA_EX} neither phase")
            nearest_phase = get_nearest_phaseV2(NIGHT_PHASE, MORNING_PHASE)

            # If nearest phase is MORNING_PHASE then sleep the computer until morning phase
            if nearest_phase[0] == "MORNING PHASE":
                logger.info(
                    "NIGHT PHASE has passed. Computer is going to sleep until: %s",
                    repr_time_delta(MORNING_PHASE["start time"]),
                )
                LAST_SLEEP_TIME_byProgram = datetime.datetime.now()
                sleep_computer_but_wake_at(MORNING_PHASE["start time"], debug=debug)
            elif nearest_phase[0] == "NIGHT PHASE":
                if _wake_up_message_sent is False:
                    _wake_up_message_sent = True

                    logger.info(
                        "MORNING PHASE's 'end time' has passed. Computer will be awake now and wait till %s.",
                        repr_time_delta(NIGHT_PHASE["start time"]),
                    )
                    while True:
                        try:
                            alert_onTelegram(
                                "Computer is awake, and internet is back up at this time.\nLast sleep time: "
                                f"`{LAST_SLEEP_TIME.strftime('%b %d %H:%M:%S')}` "
                            )
                            break
                        except requests.exceptions.ConnectionError:
                            continue
                suspend_thread_until(NIGHT_PHASE["start time"])

        # If the internet goes out early
        if go_to_sleep:
            logger.info(
                "Internet went down early than the 'end time'. going to sleep until %s...",
                repr_time_delta(
                    MORNING_PHASE["start time"]
                    if get_current_time_delta() < MORNING_PHASE["start time"]
                    else MORNING_PHASE["start time"] + datetime.timedelta(hours=24)
                ),
            )
            # LAST_SLEEP_TIME = datetime.datetime.now()
            LAST_SLEEP_TIME_byProgram = datetime.datetime.now()
            sleep_computer_but_wake_at(MORNING_PHASE["start time"], debug=debug)
            LAST_SLEEP_TIME = get_last_sleep_time()

        # If internet comes back in early
        if be_awake:
            logger.info(
                "Internet back up! will resume the program at: %s",
                repr_time_delta(NIGHT_PHASE["start time"]),
            )
            while True:
                try:
                    alert_onTelegram(
                        "Hello There!\nToday the internet came back quite early.\nLast sleep time: `{}`".format(
                            LAST_SLEEP_TIME_byProgram.strftime("%b %d %H:%M:%S")
                            if LAST_SLEEP_TIME_byProgram != datetime.datetime.min
                            else LAST_SLEEP_TIME.strftime("%b %d %H:%M:%S")
                        )
                    )
                    break
                except Exception:
                    continue
            suspend_thread_until(NIGHT_PHASE["start time"])
