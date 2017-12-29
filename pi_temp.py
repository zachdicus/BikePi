import subprocess
import re
from sense_hat import SenseHat
import numpy as np

OFFSET_LEFT = 1
OFFSET_TOP = 2

NUMS =[1,1,1,1,0,1,1,0,1,1,0,1,1,1,1,  # 0
       0,1,0,0,1,0,0,1,0,0,1,0,0,1,0,  # 1
       1,1,1,0,0,1,0,1,0,1,0,0,1,1,1,  # 2
       1,1,1,0,0,1,1,1,1,0,0,1,1,1,1,  # 3
       1,0,0,1,0,1,1,1,1,0,0,1,0,0,1,  # 4
       1,1,1,1,0,0,1,1,1,0,0,1,1,1,1,  # 5
       1,1,1,1,0,0,1,1,1,1,0,1,1,1,1,  # 6
       1,1,1,0,0,1,0,1,0,1,0,0,1,0,0,  # 7
       1,1,1,1,0,1,1,1,1,1,0,1,1,1,1,  # 8
       1,1,1,1,0,1,1,1,1,0,0,1,0,0,1]  # 9

class PiTemp():
    def __init__(self):
        self.sense = SenseHat()
        self.scale_factor = 4

    def get_cal_temp(self):
        temp = self.sense.get_temperature()
        pres_temp = self.sense.get_temperature_from_pressure()
        pi_temp = PiTemp.get_cpu_temp()

        cal_temp = PiTemp.CtoF(temp - ((pi_temp - temp) / self.scale_factor))
        cal_pres_temp = PiTemp.CtoF(pres_temp - ((pi_temp - pres_temp)
            / self.scale_factor))
        avg_temp = ((cal_temp + cal_pres_temp) / 2)

        print("Temp was {} adjusted for CPU temp of {}. Cal Temp {}".format(
            PiTemp.CtoF(temp), PiTemp.CtoF(pi_temp), cal_temp))
        print("Pres Temp was {} adjusted for CPU temp of {}. Cal Temp {}".format(
            PiTemp.CtoF(pres_temp), PiTemp.CtoF(pi_temp), cal_pres_temp))

        return cal_temp, cal_pres_temp, avg_temp
    
    @staticmethod
    def get_gpu_temp():
        reg_exp = re.compile("temp=(.+)'C")
        proc = subprocess.Popen(["/opt/vc/bin/vcgencmd", "measure_temp"],
                                stdout=subprocess.PIPE)
        out, errs = proc.communicate(timeout=2)
        out = out.decode('utf-8').strip()
        match = reg_exp.match(out)
        return float(match.group(1))

    @staticmethod
    def get_cpu_temp():
        proc = subprocess.Popen(["cat", "/sys/class/thermal/thermal_zone0/temp"],
                                stdout=subprocess.PIPE)
        out, errs = proc.communicate(timeout=2)
        temp = float(out.decode('utf-8').strip()) / 1000
        return temp

    @staticmethod
    def CtoF(temp):
        return temp * (9/5) + 32

    @staticmethod
    def FtoC(temp):
        return temp -32 * (5/9)

    @staticmethod
    def M2toMPH(speed):
        return speed * 2.23694

    @staticmethod
    def MPHtoM2(speed):
        return speed / 2.23694

    def GtoMPH(speed):
        return PiTemp.M2toMPH(speed * 9.8)

    def show_digit(self, val, xd, yd, r, g, b):
      offset = val * 15
      for p in range(offset, offset + 15):
        xt = p % 3
        yt = (p-offset) // 3
        self.sense.set_pixel(xt+xd, yt+yd, r*NUMS[p], g*NUMS[p], b*NUMS[p])

    def show_number(self, val, r, g, b):
      abs_val = abs(val)
      tens = abs_val // 10
      units = abs_val % 10
      if (abs_val > 9): self.show_digit(tens, OFFSET_LEFT, OFFSET_TOP, r, g, b)
      self.show_digit(units, OFFSET_LEFT+4, OFFSET_TOP, r, g, b)

    def get_speed(self):
        total_samples = 50
        samples = np.zeros(shape=(total_samples))
        sample = 0
        while True:
            raw = self.sense.get_accelerometer_raw()
            #print("x: {x}, y: {y}, z: {z}".format(**raw))
            x = raw['x']
            if sample >= total_samples:
                mph = int(PiTemp.GtoMPH(np.average(samples)))
                self.sense.clear()
                #self.sense.show_message("{} mph".format(mph), scroll_speed = .05)
                self.show_number(mph, 200, 0, 60)
                #print(np.average(samples))
                sample = 0
            else:
                samples[sample] = np.abs(np.abs(x) - .01275)
                #print("Sample {} is {}".format(sample, samples[sample]))
                sample+=1
            #y = PiTemp.GtoMPH(raw['y'])
            #z = PiTemp.GtoMPH(raw['z'] - 1)
            #print("x: {0}, y: {1}, z: {2}".format(x, y, z))

