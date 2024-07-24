import time
from serial import Serial
import serial.tools.list_ports
import threading
from datetime import datetime
from pathlib import Path


def find_usb_device(device_name="USB Serial Device"):
    for port in serial.tools.list_ports.comports():
        if device_name in port.description:
            device_dict = {"USB Serial Device": "Lock",
                            "CH340": "Robot"}
            msg_title = f"Connected to {device_dict[device_name]}"
            msg = f"Established connection to {device_name} using COM {port.device[3:]}."
            try:
                Log.Message(msg_title, msg)
            except NameError:
                print(f"{msg_title}. {msg}")
            return port.device[3:]
    raise ConnectionError(f"Could not find COM device {device_name}")


class RobotCommander:
    def __init__(self):
        self.COMPort = find_usb_device(device_name="CH340")
        self.serial = Serial("COM" + self.COMPort, 115200, timeout=1)
        self.startUpImports()
        self.init_log_file()

    def startUpImports(self):
        self.runCommand(["import source.RobotTester"])
    
    def init_log_file(self):
        start_time = datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
        log_dir_path = Path(__file__).resolve().parent / "Logs"
        log_file_name = f'cycle_test_logs_{start_time}.txt'
        log_dir_path.mkdir(parents=True, exist_ok=True)

        self.log_file_path = log_dir_path / log_file_name

    def presentCard(self, slot, num=1, press_dur=1500, retract_dur=2000):
        command = f"rob.presentCard({slot}, {num}, {press_dur}, {retract_dur})"
        self.runCommand([command])
        total_time = num * (press_dur + retract_dur + 1000) / 1000
        time.sleep(total_time)

    def presentCardCycleTest(self, slot, num=1, press_dur=1500, retract_dur=1500):
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
        with open(self.log_file_path, 'a') as f:  # Open file in append mode
            for line in self.out:
                print(line)
                f.write(f"{line}\n")
        # Clear the output list after writing to file
        self.out.clear()


def main():
    rob = RobotCommander()
    while True:
        rob.init_log_file()
        for i in range(3):
            rob.presentCardCycleTest(slot=i, num=5000)
            time.sleep(3)


if __name__ == "__main__":
    main()

