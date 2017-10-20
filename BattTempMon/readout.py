# Program to read one wire temperature sensor data and log them to Carbon server
import os
import time
import datetime
import subprocess
import socket
import decimal
import commands
import array

CARBON_SERVER = '127.0.0.1'
CARBON_PORT = 2003
DELAY = 15  # secs

# load required kernel modules
os.system('sudo modprobe w1-gpio')
os.system('sudo modprobe w1-therm')

# read the temperature data
def read_temp_raw(fname):
        catdata = subprocess.Popen(['cat',fname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = catdata.communicate()
        out_decode = out.decode('utf-8')
        return out_decode

# padding to maintain consistent readouts
def pad(str):
        if len(str) == 4: return " " + str
        if len(str) == 3: return "  " + str
        if len(str) == 5: return str

# send message to Graphite server
def send_msg(message):
    sock = socket.socket()
    sock.connect((CARBON_SERVER, CARBON_PORT))
    sock.sendall(message)
    sock.close()

# data gathering interval
dataInterval = 0.1

# main loop
while True:
        string = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + ','
        strArray = []
        sensorLookupDict = {}
        readTemps = {}

        # sensorIdTable stores the list of device IDs to maintain ordering if sensors are added/removed
        # read the sensorIDs from the file
        if os.path.isfile("sensorIdTable") == True:
                sensorIdTable = open("sensorIdTable", "r")
                for line in sensorIdTable:
                        splitStr = line.split()
                        sensorLookupDict[splitStr[0]] = splitStr[1]
                sensorIdTable.close()
        for filename in os.listdir("/sys/bus/w1/devices/"):
                if filename[:3] == "10-":
                        fname = '/sys/bus/w1/devices/' + filename + '/w1_slave'
                        lines = read_temp_raw(fname)

                        # sometimes the sensor won't read or the data is invalid, so retry 3 times
                        numT = 1
                        while lines.find('YES') == -1:
                                time.sleep(0.1)
                                lines = read_temp_raw(fname)
                                numT = numT + 1
                               if numT == 3: break

                        # maintaining sensorID list
                        if filename not in sensorLookupDict:
                                if os.path.isfile("sensorIdTable") == True:
                                        sensorIdTable = open("sensorIdTable", "a")
                                        numLines = max(enumerate(open("sensorIdTable")))[0]
                                        sensorIdTable.write(filename + " " + "Batt" + str(numLines + 2) + '\n')
                                        sensorIdTable.close()
                                        sensorLookupDict[filename] = "Batt" + str(numLines + 1)
                                else:
                                        sensorIdTable = open("sensorIdTable", "a")
                                        sensorIdTable.write(filename + " " + "Batt1" + '\n')
                                        sensorIdTable.close()
                                        sensorLookupDict[filename] = "Batt1"

                        # check if sensor read was successful
                        if lines.find('YES') != -1:
                                f = lines.find('t=')
                                timestamp = int(time.time())
                                temp = str(round(float(lines[f + 2:])/1000.0,0))
			# printout to test script output
			# print sensorLookupDict[filename] + ", " + temp + ", " + string
                                message = '%s %s %d\n' % (sensorLookupDict[filename], temp, timestamp)
                                send_msg(message)
                        else:
                                readTemps[sensorLookupDict[filename]] = "ERR"
