## Base/User configuration

---

- Get configuration from user in the form of a YAML file
  - Thought/Planned keys:
    ```YAML
    ssid: WiFi Name
    night phase:
        start time: HH:MM
        end time: HH:MM
    morning phase:
        start time: HH:MM
        end time: HH:MM
    timeout: 500
    ```

## Planned Logic

---

- Check if are we in the night phase.

  - if yes, then see if we're connected to the wifi or not
    - if connected to wifi, then go to sleep or something and check back again in `TIMEOUT` seconds
    - if not connected to wifi, then wait for `wifi_disconnect_timeout` for wifi to kick back in, otherwise the computer goes to sleep
  - set a <u> wake timer </u> for `morning phase -> start time`

- In the morning phase, when computer wakes up:

  - _[OPTIONAL, already set Ubuntu to auto suspend on 30min w/o power]_ check if power is connected. if computer is idle for some time go to sleep with a waketimer of some more seconds

  - check if computer is conneced to the wifi
    - if yes. very good 🐶 . our task here is done. \
      suspend the program or something.
    - if not connected, repeat the night phase process again to see if wifi is back up or not and then go to sleep setting up a wake timer of some time to check again.
