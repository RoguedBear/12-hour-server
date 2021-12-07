# 12-hour-server
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![](https://img.shields.io/github/license/RoguedBear/12-hour-server)](LICENSE)



> a python script to put the home "server" to sleep when wifi is disconnected at night, and wake up early the next day

Note: This script will only run on Linux (more specifically on Ubuntu/Debian). **WILL NOT RUN ON WINDOWS**

## What does this script do?


if you have an old computer/laptop you use as your home server, 
but don't quite want it to run 24x7, but rather only when your internet (router) is active.

In other words:
- Computer should go to sleep when you turn off your router
- Computer should wake up when you turn on your internet router

This is what this program does.

## How to use it?

---
- Clone the repository
- Make a file `config.yaml` whose contents should be same as in [config[TEMPLATE].yaml](config%5BTEMPLATE%5D.yaml):
    ```yaml
    # wired, wireless, any: connection type you want the program to check for internet connectivity
    connection type: any

    # Provide time in 24hr format
    night phase:
      start time: 23:20
      end time: 23:40
      # this timeout will be used as the frequency to check internet connectivity
      timeout: 7 # seconds
    morning phase:
      start time: 8:30
      end time: 10:30
      # this timeout will be used as the frequency to check internet connectivity
      timeout: 300 # seconds

    # This timeout will be used to change the default timeout.
    timeout: 90

    # connectivity function *optional, by default uses v2
    # you probably don't even need this in your config. Refer advanced usage
    connectivity_method: 'v2' # one of 'v2', 'v3', 'v2+v3'

    # If this key is present, program's thread would periodically wake up, check phases again and set a backup wake timer
    # of this interval (or less).
    sleep_interval: 1800 # seconds

    logging level: 10 # 10 for DEBUG, 20 for INFO, 30 for WARNING, 40 for ERROR, 50 for CRITICAL logging level

    # Optional
    telegram:
      BOT_TOKEN: YOUR TOKEN HERE
      CHAT_ID: YOUR CHAT ID HERE

    ```
- Install requirements.txt: `pip install -r requirements.txt`
- Run `./smart_sleep.py` from repository root. Make sure you have python3.8+ \
**Note: Program will run as [sudo] because the underlying command `rtcwake` which sets waketimers needs [sudo] to run**

## Viewing logs


The program creates 2 log files. one containing the normal logs (`logs.log`), and the other containing the ANSI color codes (`logs_color.log`)
If you want to see the logs of this program by ssh-ing into the server computer, then there are 2 ways for that:

1) [To view logs with color] `less -R +F Path_to_repository_root/logs/logs_color.log`
2) [To view plain logs without color] `tail -f Path_to_repository_root/logs/logs.log`

## Reporting Issues:

I haven't polished the program and fixed every bug because i needed this script to be made fast according to my needs.
If you encounter any bugs, feel free to open an issue or a pull request.

**Disclaimer to \*Potential\* Contributors: This script is unnecessarily long and i apologise for that**

## Advanced Usage

### Connectivity methods

up until release [v1.1.0-lw](https://github.com/RoguedBear/12-hour-server/releases/tag/v1.1.0-lw), the program used a
method called `check_connected_to_internetV2`. This is the v2 method which checks for internet connectivity by
polling `carrier` & `operstate` in directory `/sys/class/<your network device name>/`

Since i moved onto a complex network setup involving a secondary router that acts as a DHCP relay, `operstate`
& `carrier` both showed `up`/`1` as their output. even if the main router was down and the device had no IP address
assigned to it.

So to make the script work, the v3 method (`check_connected_to_internetV3`), now pings the default gateway to check if
main router is still up or not.

You'd be fine with using `connectivity_method` as `v2` as long as the device connects to the main router. Or, you can
switch to using the ping method by setting `connectivity_method` to `v3` if you want that. at the time of writing,
haven't put the ping method to much irl use and the v2 method works just as fine.

## Known issue:

- the timings are right, but the date could be off. since im using `timedelta` instead of `time` or `datetime`. too far
  into the project, not gonna bother changing it until i get an issue or pull request about it ¯\_(ツ)_/¯
