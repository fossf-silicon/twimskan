

# --------------------------------------
#     arm_sleeve
# --------------------------------------
from floe import FP
from parameters.CANBus import CANBus
from parameters.AS5048BEncoder import AS5048BEncoder
from parameters.NeoAnimations import NeoAnimations
from parameters.NeoPixel import NeoPixel
from parameters.FileReceiver import FileReceiver
from parameters.DigitalOutput import DigitalOutput
from parameters.ESP32Core import ESP32Core
from parameters.DigitalInput import DigitalInput
from parameters.Rainbow import Rainbow
from parameters.HbtLed import HbtLed
from parameters.I2C import I2C
def setup(iris):
  AS5048BEncoder(name="phi_encoder", pid=62930, adr=64, invert=True, offset=4707, ring_size=16, i2c=FP(3548), datatype="rgb", debug=False, active=True, bcast=True, iris=iris)
  AS5048BEncoder(name="theta_encoder", pid=59289, adr=67, invert=True, offset=-7278, ring_size=16, i2c=FP(3548), datatype="rgb", debug=False, active=True, bcast=True, iris=iris)
  CANBus(name="CANBus", pid=6545, rx=16, tx=4, adr=30, bus=0, baud=250000, rx_queue=25, terminal_debug=False, debug=False, active=True, bcast=False, iris=iris)
  DigitalInput(name="button_a", pid=39254, pin=32, pullup="pullup", debounce=200, invert=True, initial_value=False, datatype="bool", debug=True, active=True, bcast=True, iris=iris)
  DigitalInput(name="button_b", pid=16276, pin=33, pullup="pullup", debounce=200, invert=True, initial_value=False, datatype="bool", debug=True, active=True, bcast=True, iris=iris)
  DigitalInput(name="function_button", pid=2276, pin=36, pullup="None", debounce=200, invert=True, initial_value=False, datatype="bool", debug=False, active=True, bcast=True, iris=iris)
  DigitalOutput(name="DigitalOutput", pid=25716, pin=2, invert=False, initial_value=False, datatype="bool", debug=False, active=True, bcast=False, iris=iris)
  ESP32Core(name="ESP32Core", pid=6074, hbt_led=FP(55894), neo_status=FP(47403), function_button=FP(2276), bus=FP(6545), zorg=None, wifi=False, debug=False, active=True, bcast=False, iris=iris)
  FileReceiver(name="FileReceiver", pid=65000, debug=False, active=True, bcast=True, iris=iris)
  HbtLed(name="hbt_led", pid=55894, pin=5, delay=1000, datatype="int16", debug=False, active=True, bcast=False, iris=iris)
  I2C(name="I2C", pid=3548, sda=22, scl=23, bus=0, baud=400000, debug=False, active=True, bcast=False, iris=iris)
  NeoAnimations(name="phi_animation", pid=15958, neo=FP(45366), animations=FP(39389), delay=100, initial_value=1, datatype="int16", debug=False, active=True, bcast=False, iris=iris)
  NeoAnimations(name="theta_animation", pid=31372, neo=FP(1412), animations=FP(19236), delay=100, initial_value=1, datatype="int16", debug=False, active=True, bcast=False, iris=iris)
  NeoPixel(name="neo_status", pid=47403, pin=17, number_of_pixels=1, datatype="rgb", debug=False, active=True, bcast=False, iris=iris)
  NeoPixel(name="phi_ring", pid=45366, pin=21, number_of_pixels=12, datatype="rgb", debug=False, active=True, bcast=False, iris=iris)
  NeoPixel(name="theta_ring", pid=1412, pin=13, number_of_pixels=12, datatype="rgb", debug=False, active=True, bcast=False, iris=iris)
  Rainbow(name="Rainbow", pid=39389, datatype="rgb", debug=False, active=True, bcast=False, iris=iris)
  Rainbow(name="Rainbow_1", pid=19236, datatype="rgb", debug=False, active=True, bcast=False, iris=iris)
  iris.add_hots({})

