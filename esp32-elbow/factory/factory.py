import os

default_env = '{"ap_mode": false, "station_mode": false, "wifi_ssid": null, "wifi_password": null}'

def boot():
    if '.env' not in os.listdir():
        with open('.env', 'w') as f:
            f.write(default_env)

def reset():
    with open('.env', 'w') as f:
        f.write(default_env)
      