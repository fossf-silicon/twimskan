from parameters.Parameter import Parameter
from floe import Iris, Bifrost
import os
import json
import network
import time

class ESP32Core(Parameter):
    def __init__(self, *, 
                 pid, 
                 name,
                 bus, 
                 function_button, 
                 neo_status, 
                 hbt_led, 
                 terminal:bool=False, 
                 wifi,
                 iris, 
                 **k):
        super().__init__(pid=pid, iris=iris, **k)
        self.name = name
        self.bus = bus
        self.terminal = terminal
        self.function_button = function_button
        self.neo_status = neo_status
        self.hbt_led = hbt_led
        self.wifi = wifi
        
        self.wlan = None
        self.iris: Iris = iris
        iris.core = self
        
        
    def boot(self):
        with open('.env', 'r') as f:
                env = json.load(f)
        self.neo_status(b'\x02\x00\x00') # red
        if self.wifi:            
            if env['ap_mode'] is True:
                print('starting wifi in ap mode')
                self.setup_wifi_ap(ssid=env['wifi_ssid'], password=env['wifi_password'])
                self.neo_status(b'\x02\x04\x00')
            if env['station_mode'] is True:
                print('connecting wifi to station')
                self.connect_to_wifi_station(env['wifi_ssid'], env['wifi_password'])
                self.neo_status(b'\x00\x04\x01')  # green
            else:
                print('starting wifi to to ap setup mode')
                self.setup_wifi_ap()
                self.neo_status(b'\x02\x04\x00')  # yellow
            print(f'http://{self.wlan.ifconfig()[0]}')
            from parameters.web_server import WebServer
            WebServer(iris=self.iris)

        else:
            self.neo_status(b'\x00\x00\x00')  # off
    
    def setup_wifi_ap(self, *, ssid=None, password=None):
        self.wlan = network.WLAN(network.AP_IF)
        if ssid:
            if password:
                self.wlan.config(essid=ssid, password=password)
            else:
                self.wlan.config(essid=ssid)
        else:
            self.wlan.config(essid='evezor_setup')
        self.wlan.config(max_clients=1)
        self.wlan.active(True)
                    
    def connect_to_wifi_station(self, ssid, password):
        self.wlan =  network.WLAN(network.STA_IF)
        self.wlan.active(True)
        if not self.wlan.isconnected():
            print('connecting to network...')
            self.wlan.connect(ssid, password)
        while not self.wlan.isconnected():
            time.sleep(.5)
            print('.', end='')
        print('.')
        
