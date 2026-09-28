import serial
import time

class ArduinoInterface:

    def __init__(self):
        self.arduino = serial.Serial(port='COM3',   baudrate=115200, timeout=.1)

    def resetScore(self):
        self.arduino.write(b"RESET")

    def updateGoals(self, red, blue):
        if self.arduino.in_waiting > 0:
            raw_data = self.arduino.readline().decode("utf-8", errors="replace").split()
            if len(raw_data) >= 3:
                try:
                    red = int(raw_data[0])
                    blue = int(raw_data[2])
                except ValueError:
                    pass
        return red, blue