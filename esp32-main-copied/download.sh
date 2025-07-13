#/usr/bin/env bash
set -e

# ampy --port /dev/ttyUSB0 ls
ampy --port /dev/ttyUSB0 get /.env >.env
ampy --port /dev/ttyUSB0 get /CANBus.py >CANBus.py
ampy --port /dev/ttyUSB0 get /DigitalInput.py>DigitalInput.py
ampy --port /dev/ttyUSB0 get /DigitalOutput.py>DigitalOutput.py
ampy --port /dev/ttyUSB0 get /ESP32Core.py>ESP32Core.py
ampy --port /dev/ttyUSB0 get /FileReceiver.py>FileReceiver.py
ampy --port /dev/ttyUSB0 get /FileSender.py>FileSender.py
ampy --port /dev/ttyUSB0 get /GRBL.py>GRBL.py
ampy --port /dev/ttyUSB0 get /GRBLAxis.py>GRBLAxis.py
ampy --port /dev/ttyUSB0 get /GRBLScara.py>GRBLScara.py
ampy --port /dev/ttyUSB0 get /Gene.py>Gene.py
ampy --port /dev/ttyUSB0 get /HbtLed.py>HbtLed.py
ampy --port /dev/ttyUSB0 get /NeoPixel.py>NeoPixel.py
ampy --port /dev/ttyUSB0 get /Parameter.py>Parameter.py
ampy --port /dev/ttyUSB0 get /SDCard.py>SDCard.py
ampy --port /dev/ttyUSB0 get /ScaraKinematics.py>ScaraKinematics.py
ampy --port /dev/ttyUSB0 get /StdIn.py>StdIn.py
ampy --port /dev/ttyUSB0 get /UART.py>UART.py
ampy --port /dev/ttyUSB0 get /Variable.py>Variable.py
ampy --port /dev/ttyUSB0 get /WebsocketServer.py>WebsocketServer.py
ampy --port /dev/ttyUSB0 get /Zorg.py>Zorg.py
ampy --port /dev/ttyUSB0 get /boot.py>boot.py
ampy --port /dev/ttyUSB0 get /config.py>config.py
ampy --port /dev/ttyUSB0 get /floe.py>floe.py
ampy --port /dev/ttyUSB0 get /iris.py>iris.py
ampy --port /dev/ttyUSB0 get /main.py>main.py
ampy --port /dev/ttyUSB0 get /message.py>message.py
ampy --port /dev/ttyUSB0 get /namespace.py>namespace.py
ampy --port /dev/ttyUSB0 get /nwk.py>nwk.py
ampy --port /dev/ttyUSB0 get /subscriptions.json>subscriptions.json
ampy --port /dev/ttyUSB0 get /uaiohttp.py>uaiohttp.py


# ampy --port /dev/ttyUSB0 get /static>static
midir -p static
ampy --port /dev/ttyUSB0 get /static/about.html>static/about.html
ampy --port /dev/ttyUSB0 get /static/fancy_elements.css>static/fancy_elements.css
ampy --port /dev/ttyUSB0 get /static/parameters.js>static/parameters.js
ampy --port /dev/ttyUSB0 get /static/style.css>static/style.css
ampy --port /dev/ttyUSB0 get /static/terminal.html>static/terminal.html
ampy --port /dev/ttyUSB0 get /static/terminal.js>static/terminal.js


# ampy --port /dev/ttyUSB0 get /static/favicon.ico>static/favicon.ico
# ampy --port /dev/ttyUSB0 get /static/logo.png>static/logo.png
# ampy --port /dev/ttyUSB0 get /static/crosshair.png>static/crosshair.png



