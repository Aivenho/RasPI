import os
import glob
import time
from datetime import datetime

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
device_folder = ''
evice_file = ''

def read_temps_multi():
        base_dir = '/sys/bus/w1/devices/'
        for device in glob.glob(base_dir + '28*'):
                global device_folder
                global device_file
                device_folder = device
                device_file = device_folder + '/w1_slave'
                print(read_temp())

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = read_temp_raw()
    date = str(datetime.now())[:16]
    sensor = device_folder[-15:]
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return date, sensor, temp_c, temp_f

while True:
        read_temps_multi()
        time.sleep(1)
