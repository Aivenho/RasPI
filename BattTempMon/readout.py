# Program to read one wire temperature sensor data and log them to MySQL database
import os
import time
import datetime
import array
import urllib2
import subprocess
import MySQLdb
import RPi.GPIO as GPIO
import decimal
import commands

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

# data gathering interval
dataInterval = 5

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
			
			# sometimes the sensor won't read or the data is invalid. Try 3 times
			numT = 1
			while lines.find('YES') == -1:
				time.sleep(0.2)
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
				temp = str(round(float(lines[f + 2:])/1000.0,2))
				print temp
				if temp == "85.0": readTemps[sensorLookupDict[filename]] = "ERR"
				else: readTemps[sensorLookupDict[filename]] = temp
			else:
				readTemps[sensorLookupDict[filename]] = "ERR"

	# update the LCD and log the data
	with open("/home/pi/tempLogger/tempData", "a") as myfile:
		lcdStr = ""
		for s in range(len(sensorLookupDict)):     
			print s
			if "Batt" + str(s+ 1) in readTemps:
				string = string + readTemps["Batt" + str(s+ 1)] + ','
			else:
				string = string + "ERR" + ','
			print string
		lcdOrderArray = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
		for s in lcdOrderArray:
			if "Batt" + str(s) in readTemps: 
				lcdStr = lcdStr + "Batt" + str(s) + ":" + pad(readTemps["Batt" + str(s)]) + "  "
			else:
				lcdStr = lcdStr + "Batt" + str(s) + ":" "ERR  " + "  "
		print lcdStr
		print string[:-1]
		time.sleep(dataInterval)

	# Send data to MySQL server		
	def sendDataToServer():
	global temperature

	threading.Timer(600,sendDataToServer).start()
	print("Sensing...")
	readSensor()
	temperature = round(temperature,1)
	print(temperature)
    temp= "%.1f" %temperature
	urllib2.urlopen("http://www.educ8s.tv/weather/add_data.php?temp="+temp).read()

sendDataToServer()
