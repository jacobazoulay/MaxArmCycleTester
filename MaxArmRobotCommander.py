import time

import numpy as np
from serial import Serial
import serial.tools.list_ports
import threading
from datetime import datetime
import matplotlib.pyplot as plt
from RGB_Vals import *


def find_usb_device(device_name="USB Serial Device"):
    for port in serial.tools.list_ports.comports():
        if device_name in port.description:
            try:
                device_dict = {"USB Serial Device": "Lock",
                               "CH340": "Robot"}
                Log.Message(f"Connected to {device_dict[device_name]}",
                            f"Established connection to {device_name} using COM {port.device[3:]}.")
            except NameError:
                pass
            return port.device[3:]
    raise ConnectionError(f"Could not find COM device {device_name}")


class RobotCommander:
    def __init__(self):
        self.COMPort = find_usb_device(device_name="CH340")
        self.serial = Serial("COM" + self.COMPort, 115200, timeout=1)
        self.startUpImports()
        self.start_time = datetime.now().strftime('%Y_%m_%d__%H_%M_%S')

    def startUpImports(self):
        self.runCommand(["import source.RobotTester"])

    def presentCard(self, slot, num=1, press_dur=1500, retract_dur=2000):
        command = f"rob.presentCard({slot}, {num}, {press_dur}, {retract_dur})"
        self.runCommand([command])
        total_time = num * (press_dur + retract_dur + 1000) / 1000
        time.sleep(total_time)

    def presentCardCycleTest(self, slot, num=1, press_dur=1500, retract_dur=2000):
        self.startThreadRead()
        command = f"rob.presentCard({slot}, {num}, {press_dur}, {retract_dur})"
        self.runCommand([command], readOut=False)
        total_time = num * (press_dur + retract_dur + 1000) / 1000
        time.sleep(total_time)
        self.stopThreadRead()

    def resetRobot(self):
        self.serial.write(b'\x04')
        time.sleep(4)
        self.readOut()

    def haltExecution(self):
        self.serial.write(b'\x03')
        self.readOut()

    def runCommand(self, cmds, readOut=True):
        for i, cmd in enumerate(cmds):
            cmd = (cmd + '\r').encode()
            self.serial.write(cmd)
            if readOut:
                self.serial.read_until(cmd + b'\n')
                if i < len(cmds) - 1:
                    self.readOut()

    def readOut(self):
        out = self.serial.read_until(b'>>> ')
        out = out[:-4].decode("utf-8").replace('\r\n', '\n')
        return out

    def stopThreadRead(self):
        self.thread = False

    def startThreadRead(self):
        self.thread = True
        self.out = []

        def readOutLoop():
            while self.thread:
                line = self.serial.readline().decode().rstrip()
                if line == "": continue
                formatted_datetime = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
                line = formatted_datetime + " " + line

                self.out.append(line)
                self.writeToFile()

        t = threading.Thread(target=readOutLoop)
        t.start()

    def writeToFile(self):
        with open(f'cycle_test_logs_{self.start_time}.txt', 'a') as f:  # Open file in append mode
            for line in self.out:
                print(line)
                f.write(f"{line}\n")
        # Clear the output list after writing to file
        self.out.clear()


def plotRGB(grntd_or_dec):
    if grntd_or_dec == "g":
        meas = granted
        title = "Granted"
    elif grntd_or_dec == "d":
        meas = declined
        title = "Declined"
    elif grntd_or_dec == "y":
        meas = yellow
        title = "Yellow"
    elif grntd_or_dec == 'l':
        meas = lockout
        title = "Lockout"
    elif grntd_or_dec == 't':
        meas = test_data
        title = 'Test'
    else:
        meas = none
        title = "No Read"
    rs = [rgb[0] for rgb in meas]
    gs = [rgb[1] for rgb in meas]
    bs = [rgb[2] for rgb in meas]
    xs = range(len(meas))

    plt.plot(xs, rs, color='red', label='Red')
    plt.plot(xs, gs, color='green', label='Green')
    plt.plot(xs, bs, color='blue', label='Blue')
    plt.title(f'RGB Values - {title}')
    plt.xlabel("Measurement Number")
    plt.ylabel("Intensity")
    plt.legend()
    plt.ylim((0, 1200))

    plt.show()

    maxs = max(meas, key=lambda x: max(x))
    if grntd_or_dec == "l":
        maxs = meas[130]
    print(f"({round(maxs[0] / max(maxs), 2)}, {round(maxs[1] / max(maxs), 2)}, {round(maxs[2] / max(maxs), 2)})")


def plotRGBReads():
    plotRGB('t')
    plotRGB('d')
    plotRGB('g')
    plotRGB('l')
    plotRGB('y')
    plotRGB('n')


def main():
    rob = RobotCommander()
    rob.presentCardCycleTest(slot=0, num=10)


if __name__ == "__main__":
    main()
