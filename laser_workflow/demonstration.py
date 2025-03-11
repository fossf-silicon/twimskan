
from PyQt6 import QtCore, QtWidgets, uic
import sys
import os
import gdsfactory as gf
import subprocess

from gdsfactory.export.to_svg import (
    to_svg,
)
from gdsfactory.typings import Layer

svg_filename = "/tmp/current_job.svg"


def sendToGDS(name):
    c = gf.Component()
    ref1 = c.add_ref(gf.components.rectangle(size=(10, 10), layer=(1, 0)))
    ref2 = c.add_ref(gf.components.text(name, size=10, layer=(2, 0)))

    ref1.xmax = ref2.xmin - 5
   
    # Step 3: Call the to_svg function
    to_svg(
        component=c,
        exclude_layers=None,  # No layers excluded
        filename=str(svg_filename),
        scale=2.5,  # No scaling
    )

    c.show()

def sendToLaser(file_name):
    # We may need to do some SVG transformations here, specifically to specify job paths etc.
    # Also calling a bash file to ensure we set up a proper venv for meerk40t

    # Expect firelaser.sh to be in the same location as the demonstation.py
    laser_shell_location = os.path.join(os.getcwd(), "firelaser.sh")
    laser_shell_command = os.path.abspath(laser_shell_location) 

    subprocess.run([laser_shell_command, file_name]) 
    # Most likely this will return right away, so we really ought to delay to allow burning and robot arming
    # TODO: Make a robot do it's thing, but, this is asynchronous burning. You will need a reasonable delay to allow the firing laser to finish.


class Ui_MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./waferburn.ui', self)
        self.pushButton.clicked.connect(self.takeinputs)
    
    def takeinputs(self):
        name, done1 = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter your name:') 
        if done1:
             # TODO: Tell robot to grab wafer
             # Showing confirmation message along
             # with information provided by user. 
             sendToGDS(name)
             
             sendToLaser(svg_filename)

             # Hide the pushbutton after inputs provided by the use.
             

if __name__ == "__main__": 
    app = QtWidgets.QApplication(sys.argv)

    window = Ui_MainWindow()
    window.show()
   
    sys.exit(app.exec()) 

