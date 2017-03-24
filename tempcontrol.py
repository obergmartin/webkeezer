from datetime import datetime
from time import time, sleep
from os import popen, system, path
import csv
import json
import threading
from json import encoder

encoder.FLOAT_REPR = lambda x: format(x, '.1f')

data_dir = '/root/webkeezer/'
floorPin = 11

TEMP_DELAY = 60 #
RELAY_DELAY = 20*60 # 20 minutes * 60 seconds
EMAIL_DELAY = 15*60

PARAM_FILE = 'keezerparams.txt'
global log_keys

log_keys = ['time', 'temp1C', 'temp2C', 'setpoint', 'relayState', 'floorState']

#RELAY_PIN = 18

t_id1 = "28-0000045d835b"
t_id2 = "28-0000045c9ecc"

main_thread = threading.Event()


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
    to_find = p+' is '
    # finding "11 is " len = 4 or 5
    #     0123456
    # Pin 11 is LOW
    # get index of the next character:
    n = result.find(to_find) + len(to_find)
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
    to_find = "state: O"
    # finding "state: O"
    #                  012345678
    # > Reading RELAY0 state: ON
    n = result.find(to_find) + len(to_find)
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


def makeFileName():
    dt = datetime.now()
    #yr, wk, _ = dt.isocalendar()
    yr = dt.year
    mth = '{:0>2}'.format(dt.month)
    dd = '{:0>2}'.format(dt.day)
    #fn = "keezerdata/%d_%d.txt"%(yr, wk)
    fn = data_dir+"%s%s%s.txt"%(yr, mth, dd)
    return fn


def getDateTime():
    dt = datetime.now()
    mth = '{:0>2}'.format(dt.month)
    dd = '{:0>2}'.format(dt.day)
    yday = str(dt.timetuple().tm_yday)
    hh = '{:0>2}'.format(dt.hour)
    hh = str(dt.hour)
    mm = '{:0>2}'.format(dt.minute)
    
    d = '.'.join([mth, dd])
    t = ':'.join([hh, mm])

    return [d,t]


def makeTimeStamp():
    [d, t] = getDateTime()
    return '-'.join([d, t])


def writeJSON():
    def parseRow(r):
        pr = []
        for i,c in enumerate(r):
            if len(c) == 0:
                # use previous value
                pr.append(dat[-1][i])
            else:
                if i == 0:
                    # for time
                    pr.append(c)
                elif i >= 4:
                    # for relay states: 0,1
                    pr.append(str(int(c)))
                else:
                    # for temperatures with 1 decimal place
                    pr.append(str(round(float(c),1)))
        return pr

    dat = []
    with open(makeFileName(), 'r') as f:
        c = csv.reader(f)
        for row in c:
            dat.append(parseRow(row))
    
    jtm = 'ts=' + json.dumps([i[0] for i in dat])+'\n'
    jt1 = 't1=' + json.dumps([i[1] for i in dat])+'\n'
    jt2 = 't2=' + json.dumps([i[2] for i in dat])+'\n'
    jon = 'rel='+ json.dumps([i[4] for i in dat])+'\n'
    
    with open(data_dir+'plotdata.json', 'w') as f:
        f.write(jtm)
        f.write(jt1.replace('"',''))
        f.write(jt2.replace('"',''))
        f.write(jon.replace('"',''))


def getKeezerParams():
    with open(PARAM_FILE, 'r') as f:
        try:
            setpoint = float(f.readline().strip())
        except:
            print "invalid setpoint in line 1 of " + PARAM_FILE
            return -100
        try:
            deltaT = float(f.readline().strip())
        except:
            print "invalid deltaT in line 2 of " + PARAM_FILE
            return -1
    return setpoint, deltaT


def getRecentData():
    [d, t] = getDateTime()

    lastDat = {
        'time'      : t, 
        'temp1C'    : -999,
        'temp2C'    : -999,
        'setpoint'  : -999, 
        'relayState': -999,
        'floorState': -999
        }

    try:
        with open(data_dir+'recent.json', 'r') as f:
            # start at 7 to ignore "data = "
            recent = json.loads(f.readline().strip()[7:])
    except:
        recent = {}

    # overwrite default 'null' values    
    for k in recent.keys():
        lastDat[k] = recent[k]

    return lastDat
    

def writeRecent(d):
    #print d
    s = "data = {"
    s += '"date":{!r},'.format(d['date'])
    s += '"time":{!r},'.format(d['time'])
    s += '"temp1C":{0:.1f},'.format(d['temp1C'])
    s += '"temp2C":{0:.1f},'.format(d['temp2C'])
    s += '"setpoint":{0:.1f},'.format(d['setpoint'])
    s += '"relayState":{},'.format(d['relayState'])
    s += '"floorState":{},'.format(d['floorState'])
    s += '"lastRelayOff":{}'.format(d['lastRelayOff'])
    s += '}\n'

    print s
    
    #j = json.JSONEncoder()
    #s = 'data = ' + j.encode(d) + '\n'
    
    # write new recent data
    with open(data_dir+'recent.json', 'w') as f:
        f.write(s)


def writeLog(d):
    # append to the log file
    with open(makeFileName(), 'a') as f:
        ln = ','.join([str(d[i]) for i in log_keys])
        #print 'appending'
        #print ln
        #ln = ','.join([str(i) for i in [c1, c2, s, r, fl]])+'\n'
        f.write(ln + '\n')


def run():
    global lastDat
    global last_relay_off

    curDate, curTime = getDateTime()
    # need to read each time in case of change
    setpoint, deltaT = getKeezerParams()
    
    # get current floor state
    floorState = getPinStatus(floorPin)
    print "floor is", floorState
    if floorState:
        pass#sendFloodEmail()
    
    # get current relay state
    relayState = getRelayStatus()
    states = ["off", "on"]
    print "relay is %s"%states[relayState]

    # get current temperatures
    temp1C = round(getTemp(t_id1), 1) 
    temp2C = round(getTemp(t_id2), 1)
    print "temperature 1 is %s"%temp1C
    print "temperature 2 is %s"%temp2C
    print "setpoint is %s"%setpoint
    
    # make relay decision based on tempC
    if temp1C > (setpoint + deltaT):
        # make sure relay doesn't cycle too frequently
        if relayState == 0 and time() - last_relay_off > RELAY_DELAY:
            if time() - last_relay_off > RELAY_DELAY:
                setRelayOn()
                print "turning relay on"
                relayState = 1
            else:
                print "not enough time to cycle freezer"
    elif temp1C < setpoint:
        if relayState == 1:
            setRelayOff()
            last_relay_off = time()
            print "turning relay off"
            relayState = 0
    
    curDat = {
        'date': curDate,
        'time': curTime, 
        'temp1C'      : temp1C,
        'temp2C'      : round(temp2C,1),
        'setpoint'    : setpoint, 
        'relayState'  : relayState,
        'floorState'  : floorState,
        'lastRelayOff': last_relay_off
        }
              
    # Write to log file
    # set to '' if repeats
    # append data to log file
    data_filename = makeFileName()
    if path.isfile(data_filename):
        logVals = ['' if curDat[k] == lastDat[k] else curDat[k] for k in log_keys]
    else:
        logVals = [curDat[k] for k in log_keys]

    logDat = dict(zip(log_keys, logVals))
    if logDat['temp1C'] != '':
        logDat['temp1C'] = round(logDat['temp1C'],1)
    #print logDat
    writeLog(logDat)
    
    # Write recent data for plotting
    writeRecent(curDat)
    writeJSON()
    
    # copy data for next round
    lastDat = curDat.copy()
    print ""


def main():
    sleep(TEMP_DELAY-datetime.now().second)
    while True:
        run()
        # wait for next reading
        #main_thread.wait(timeout=TEMP_DELAY-datetime.now().second)
        sleep(TEMP_DELAY-datetime.now().second)


lastDat = getRecentData()
last_relay_off = 0

main()




