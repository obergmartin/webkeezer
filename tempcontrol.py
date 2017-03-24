from os import popen, system, path
from datetime import datetime
import csv
import json

data_dir = '/root/webkeezer/'
floorPin = 11
relayPin = 18
	
def getTemp(w1id):
	#https://wiki.onion.io/Tutorials/Reading-1Wire-Sensor-Data
	cmd = "cat /sys/devices/w1_bus_master1/"+w1id+"/w1_slave"
	#http://stackoverflow.com/questions/3503879/assign-output-of-os-system-to-a-variable-and-prevent-it-from-being-displayed-on
	result = popen(cmd).read()
	t = int(result[result.find('t=')+2:])/1000.
	return t

	
def getPinStatus(pinN):
	p = str(pinN)
	cmd = "gpioctl get "+p
	result = popen(cmd).read()
	to_find = p+' is'
	# this may not work with single digit pin numbers...
	n = result.find(to_find) + 6 
	#print result[n]
	if result[n] == 'L':
		state = 0
	else:
		state = 1	
	return state

def getRelayStatus():
	cmd = "relay-exp read 0"
	result = popen(cmd).read()
	#print result
	to_find = "state: "
	# finding "state: "
	#                  012345678
	# > Reading RELAY0 state: ON
	n = result.find(to_find) + 8
	if result[n] == 'N': 
		state = 1
	else:
		state = 0
	return state

	
def setRelayOn():
	#cmd = "gpioctl dirout-high "+str(relayPin)
	cmd = "relay-exp 0 on"
	system(cmd)


def setRelayOff():
	#cmd = "gpioctl dirout-low "+str(relayPin)
	cmd = "relay-exp 0 off"
	system(cmd)

	
def sendWarmEmail():
	cmd = "sh email_tempwarning.sh"
	#system(cmd)


def sendFloodEmail():
	cmd = "sh email_floodwarning.sh"
	#system(cmd)


def makeFileName():
	dt = datetime.now()
	#yr, wk, _ = dt.isocalendar()
	yr = dt.year
	mth = '{:0>2}'.format(dt.month)
	dd = '{:0>2}'.format(dt.day)
	#fn = "keezerdata/%d_%d.txt"%(yr, wk)
	fn = data_dir+"%s%s%s.txt"%(yr, mth, dd)
	return fn


def makeTimeStamp():
	dt = datetime.now()
	mth = '{:0>2}'.format(dt.month)
	dd = '{:0>2}'.format(dt.day)
	yday = str(dt.timetuple().tm_yday)
	hh = '{:0>2}'.format(dt.hour)
	hh = str(dt.hour)
	mm = '{:0>2}'.format(dt.minute)
	
	d = '.'.join([mth, dd])
	t = ':'.join([hh, mm])
	
	return '-'.join([d, t])

	
def writeJson():
	def parseRow(r):
	    pr = []
	    for i in r:
	        if len(i) == 0:
	            pr.append('null')
	        else:
	            pr.append(float(i))
	    return pr

	dat = []
	with open(makeFileName(), 'r') as f:
	    c = csv.reader(f)
	    for row in c:
	        dat.append(parseRow(row))
	
	jt1 = 't1='+json.dumps([i[0] for i in dat])+'\n'
	jt2 = 't2='+json.dumps([i[1] for i in dat])+'\n'
	jon = 'rel='+json.dumps([i[3] for i in dat])+'\n'
	
	with open(data_dir+'plotdata.json', 'w') as f:
	    f.write(jt1.replace('"',''))
	    f.write(jt2.replace('"',''))
	    f.write(jon.replace('"',''))


def getKeezerParams():
	with open('keezerparams.txt', 'r') as f:
		try:
			setpoint = float(f.readline().strip())
		except:
			print "invalid setpoint in line 1 of keezerparams.txt"
			return -100
		try:
			deltaT = float(f.readline().strip())
		except:
			print "invalid deltaT in line 2 of keezerparams.txt"
			return -1
	return setpoint, deltaT


def getRecentData():
	try:
		with open(data_dir+'recent.json', 'r') as f:
			exec(f.readline().strip())
		#print 'recent', data
		last_tempC, last_temp2C, last_setpoint, last_relayState, last_floorState = [data[i] for i in ['tempC', 'temp2C', 'setpoint', 'relayState', 'floorState']]
	except:
		last_tempC, last_temp2C, last_setpoint, last_relayState, last_floorState = -999,-999,-999, -999, -999
	
	return last_tempC, last_temp2C, last_setpoint, last_relayState, last_floorState
	
	
def main():
	setpoint, deltaT = getKeezerParams()
	if setpoint == -100 or deltaT <= 0:
		return 0
	
	# get recent data	
	last_tempC, last_temp2C, last_setpoint, last_relayState, last_floorState = getRecentData()
	
	# get current floor state
	floorState = getPinStatus(floorPin)
	if floorState:
		sendFloodEmail()
	
	# get current relay state
	#relayState = getPinStatus(relayPin)
	relayState = getRelayStatus()
	states = ["off", "on"]
	print "relay is %s"%states[relayState]

	# get current temperatures
	t1 = "28-0000045d835b"
	t2 = "28-0000045c9ecc"
	tempC = round(getTemp(t1), 1) 
	temp2C = round(getTemp(t2), 1)
	print "temperature is %s"%tempC
	print "setpoint is %s"%setpoint
	
	if tempC > (setpoint + 3):
		sendWarmEmail()

	# make relay decision based on tempC
	if tempC > (setpoint+deltaT):
		if relayState == 0:
			setRelayOn()
			print "turning relay on"
			relayState = 1
	elif tempC < setpoint:
		if relayState == 1:
			setRelayOff()
			print "turning relay off"
			relayState = 0
	
	
	# write new recent data
	with open(data_dir+'recent.json', 'w') as f:
		dat = [str(i) for i in [makeTimeStamp(), tempC, temp2C, setpoint, relayState, floorState]]
		f.write('data = {"time":"%s","tempC":%s,"temp2C":%s,"setpoint":%s,"relayState":%s, "floorState":%s}\n'%(dat[0], dat[1], dat[2], dat[3], dat[4], dat[5]))
	
	# append data to log file
	data_filename = makeFileName()
	# collect values
	c1, c2, s, r, fl = [tempC, temp2C, setpoint, relayState, floorState]

	# set to '' if repeats
	if path.isfile(data_filename):
		if tempC == last_tempC:
			c1 = ''
		if temp2C == last_temp2C:
			c2 = ''
		if setpoint == last_setpoint:
			s = ''
		if relayState == last_relayState:
			r = ''
		if floorState == last_floorState:
			fl = ''
	# write the file
	with open(data_filename, 'a') as f:
		#ln = ','.join([makeTimeStamp(), str(tempC), str(setpoint), str(relayState)])+'\n'
		ln = ','.join([str(i) for i in [c1, c2, s, r, fl]])+'\n'
		f.write(ln)
	
	writeJson()
	
	
if __name__ == "__main__":
    # execute only if run as a script
    main()
    
    
    
    
    
    
