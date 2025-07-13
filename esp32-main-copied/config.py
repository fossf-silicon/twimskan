
# --------------------------------------
name = 'Alpha_Arm'
canvas_id = '65742b61e91836cdcanv'
# __version__ = TODO: add this
# --------------------------------------
from floe import FP

from Zorg import Zorg
from WebsocketServer import WebsocketServer
from NeoPixel import NeoPixel
from CANBus import CANBus
from StdIn import StdIn
from DigitalInput import DigitalInput
from SDCard import SDCard
from ESP32Core import ESP32Core
from GRBLScara import GRBLScara
from FileSender import FileSender
from ScaraKinematics import ScaraKinematics
from GRBLAxis import GRBLAxis
from Variable import Variable
from UART import UART
from DigitalOutput import DigitalOutput
from HbtLed import HbtLed
def setup(iris):

  CANBus(name='CANBus', pid=6545, rx=2, tx=4, adr=20, bus=0, baud=250000, rx_queue=25, terminal_debug=False, debug=False, active=True, bcast=False, iris=iris)
  DigitalInput(name='function_button', pid=2276, pin=36, pullup='None', edge_detection='None', debounce=200, invert=True, initial_value=False, datatype="bool", debug=False, active=True, bcast=True, iris=iris)
  DigitalOutput(name='can_slp', pid=32072, pin=13, invert=False, initial_value=False, datatype="bool", debug=False, active=True, bcast=False, iris=iris)
  DigitalOutput(name='x_reset', pid=11168, pin=25, invert=False, initial_value=True, datatype="bool", debug=False, active=True, bcast=False, iris=iris)
  DigitalOutput(name='y_reset', pid=40190, pin=26, invert=False, initial_value=True, datatype="bool", debug=False, active=True, bcast=False, iris=iris)
  DigitalOutput(name='z_reset', pid=37697, pin=27, invert=False, initial_value=True, datatype="bool", debug=False, active=True, bcast=False, iris=iris)
  ESP32Core(name='ESP32Core', pid=6074, wifi=True, hbt_led=FP(55894), neo_status=FP(47403), function_button=FP(2276), bus=FP(6545), zorg=FP(21885), webserver=FP(50076), debug=False, active=True, bcast=False, iris=iris)
  FileSender(name='FileSender', pid=65001, debug=False, active=True, bcast=False, iris=iris)
  GRBLAxis(name='p', pid=1410, move=None, max=150, min=-150, home=None, reset=FP(40190), debug=False, active=True, bcast=False, iris=iris)
  GRBLAxis(name='t', pid=23147, move=None, max=150, min=-150, home=None, reset=FP(11168), debug=False, active=True, bcast=False, iris=iris)
  GRBLAxis(name='z', pid=16570, move=None, max=250, min=0, home=None, reset=FP(37697), debug=False, active=True, bcast=False, iris=iris)
  GRBLScara(name='grbl', pid=11895, webserver_output=True, theta_encoder=FP(6003), phi_encoder=FP(5054), UART=FP(30101), x=FP(23147), y=FP(1410), z=FP(16570), a=None, b=None, c=None, kinematics=FP(45799), debug=False, active=True, bcast=False, iris=iris)
  HbtLed(name='hbt_led', pid=55894, pin=32, delay=1000, datatype="int", debug=False, active=True, bcast=False, iris=iris)
  NeoPixel(name='neo_status', pid=47403, pin=12, number_of_pixels=1, animation=0, delay=200, animations=None, datatype="rgb", debug=False, active=True, bcast=False, iris=iris)
  SDCard(name='SDCard', pid=25805, slot=2, auto_mount=False, debug=False, active=True, bcast=False, iris=iris)
  ScaraKinematics(name='ScaraKinematics', pid=45799, theta_length=200, phi_length=200, max_segment_size=1.0, right_handed=True, debug=False, active=True, bcast=False, iris=iris)
  StdIn(name='StdIn', pid=30472, buf_len=40, send2repl=True, datatype="string", debug=True, active=True, bcast=False, iris=iris)
  UART(name='UART', pid=30101, rx=14, tx=21, bus=1, baud=115200, encode='utf8', debug=False, active=True, bcast=False, iris=iris)
  Variable(name='phi_encoder', pid=5054, state=0, datatype="float", constant=False, debug=False, active=True, bcast=True, iris=iris)
  Variable(name='theta_encoder', pid=6003, state=0, datatype="float", constant=False, debug=False, active=True, bcast=True, iris=iris)
  WebsocketServer(name='WebsocketServer', pid=50076, datatype="null", debug=False, active=True, bcast=False, iris=iris)
  Zorg(name='Zorg', pid=21885, debug=False, active=True, bcast=False, iris=iris)
  iris.add_hots({})
  iris.set_info(canvas_id, name)


