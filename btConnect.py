# set automatic key on NXT to 1234 == use Default password, CONFIRM check-mark
# there is a way to check if the MAC is still associated with the right team.
# However, that takes 3 seconds. Thus, clear the MAC file before every event
# and / or if teams exchange bricks
# author: Michael Fruhnert, Summer 2016
#import bluetooth
from os import remove, makedirs
from os.path import exists, dirname
import subprocess as sp
import datetime

btDeviceListLoc = './MAC_BT.txt'
teamStorage = './storedData/'
maxTeamNum = 70 # number of teams in class
deviceList = [''] * maxTeamNum
# global variables not necessary, but avoids copying of variables and passing
# things along all the time. Easier for the user since we never use more than
# one device at a time.
btChannel = None # stores connection to NXT
btProtocol = None # file that stores send / received information
dataTot = b'' # stores bytes received

######################################################################
# Device Search, Pairing (most time consuming => tried to centralize)
######################################################################
def findDevice(teamName):
    teamNum = int(teamName[4:6])
    mac = checkPaired(teamName)
    if (mac == ''):
        mac = deviceList[teamNum - 1]
        if (mac == ''):
            reloadDeviceList()
            mac = deviceList[teamNum - 1]
            if (mac == ''):
                updateDeviceList()
                mac = deviceList[teamNum - 1]
                if (mac == ''):
                    print('Cannot find device')
                    return mac
        sp.call("./connect.bin " + mac, shell=True) # pair device
    return mac

def checkPaired(teamName):
    p = sp.Popen(["bt-device", "--list"], stdin=sp.PIPE,
            stdout=sp.PIPE, close_fds=True)
    (stdout, stdin) = (p.stdout, p.stdin)
    data = stdout.readlines()
    # first line either 'Added devices:' or 'No devices Found' - skip
    for i in range(1, len(data)):
        line = str(data[i])
        if (len(line) == 31):
            if (line[2:8] == teamName):
                mac = line[10:-4]
                return mac
    return '' # not found

def getLock():
    while exists(btDeviceListLoc + 'Temp'):
        print('File locked by another user.')
        sleep(0.1)
        print('Trying again.')
    open(btDeviceListLoc + 'Temp', 'w').close()
    
def removeLock():
    remove(btDeviceListLoc + 'Temp')
    
def reloadDeviceList():
    global deviceList
    # print('Reloading device list')
    if exists(btDeviceListLoc):
        getLock()
        with open(btDeviceListLoc, 'r') as file:
            deviceList = file.readlines()
        removeLock() 
        for i in range(len(deviceList)):
            deviceList[i] = deviceList[i].strip() # remove newLine etc       
    else:
        rebuildDeviceList()

def rebuildDeviceList():
    global deviceList
    getLock()
    # print('Rebuilding device list')
    deviceList = [''] * maxTeamNum
    with open(btDeviceListLoc, 'w') as file:
        for device in deviceList:
            file.write(device + '\n')   
    removeLock()
    
def updateDeviceList():
    global deviceList
    
    # print('Updating list')
    # builds a history / cache for faster loading / finding of devices
    # looks for 4 seconds and gets names (less than 2 seconds does not find things)
    nearby_devices = bluetooth.discover_devices(duration = 4,
                        lookup_names = True, flush_cache = True)

    # reload devices to be up to date
    reloadDeviceList()
    
    # search device and update list
    update = 0
    for addr, name in nearby_devices:
        if (len(name) == 6):
            if (name[0:4] == 'Team'):
                if name[4:6].isdigit():
                    teamNum = int(name[4:6])
                    if deviceList[teamNum - 1] != addr:
                        deviceList[teamNum - 1] = addr
                        print("{0} - {1} updated".format(addr, name))
                        update = 1
 
    if update:
        getLock()
        with open(btDeviceListLoc, 'w') as file:
            for device in deviceList:
                file.write(device + '\n')
        removeLock()

###################################################################
# BT connection stuff
###################################################################

def initConnection(addr, teamName):
    global btChannel, btProtocol
    filename = teamStorage + teamName + '/protocol.txt'
    # create folder if necessary
    makedirs(dirname(filename), exist_ok=True)
    btProtocol = open(filename, 'a')
    documentConnection('open', [])
    port = 1  # know from MATLAB or elsewhere
    try:
        btChannel = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        btChannel.connect((addr, port))
        btChannel.settimeout(1) # 1 seconds of reading (minimum)
    except bluetooth.btcommon.BluetoothError as err:
        # Error handler
        print('Error occured while using socket')
        return
    documentConnection('connect', [addr, teamName])
    
# Command structure valid for incoming and outgoing message (note: LSB and
# MSB are flipped compared to most applications
# Sending NXT direct messaging commands, packet structure as follows from
# LEGO Mindstorm NXT'reme Direct Commands documentation
#
# Byte 0:       Least Significant Byte of command length, 0x0A: size = 10
# Byte 1:       Most Significant Byte of command length
# Byte 2:       Command type - 0x80 = direct command telegram, no response
#                                     required from NXT
# Byte 3:       Command - 0x09 = MESSAGEWRITE
# Byte 4:       Inbox Number - 0x00 = default mailbox
# Byte 5:       Message size - 0x06 = transmission of 3 16-bit words for
#                                     use with getMessageWithParm[]
#                                     (3 words * 2 bytes = 6 bytes total)
# ---------------- Following bytes are ENGR 14X defined -------------------
# Byte 6-7:     LSB and MSB, respectively, of error being transmitted
# Byte 8-9:     LSB and MSB, respectively, of xCoord being transmitted
# Byte 10-11:   LSB and MSB, respectively, of yCoord codes being transmitted
    
def btRead():
    global dataTot
    while True:
        if (len(dataTot) < 12):
            try:
                # generally one recv should not work => use a loop
                # However, message seems to be small enough
                data = btChannel.recv(50) # size of buffer (12 Byte message)
                dataTot += data
            except: # time out error
                # print('No data received')
                return [0, 0, 0, 0] # no success

        while (len(dataTot) > 11):
            # Attempt to read metadata series  
            if (dataTot[0:6] == b'\x0A\x00\x80\x09\x00\x06'):
                # always 6 Bytes send, even with 1 Word Message
                val = [1] # add for success
                for i in range(6, 12, 2):
                    val.append(int.from_bytes(dataTot[i:i+2],
                                byteorder = 'little', signed = True))
                dataTot = dataTot[12:] # 'delete' message from buffer
                documentConnection('recv', val[1:])
                return val
            else:
                dataTot.pop(0) # for all unknown message types
                
    return [0, 0, 0, 0] # never reached, safe-guard

def btWrite(err, xCoor, yCoor):
    vals = [err, xCoor, yCoor]
    code = b'\x0A\x00\x80\x09\x00\x06' # same metadata (see comment above)
    for i in vals:
        code += i.to_bytes(2, byteorder = 'little', signed = True)
    #btChannel.send(code)
    #documentConnection('sent', vals)

    return code

def documentConnection(action, vals):
    if (action == 'recv'):
        # text = 'Received: ' + str(vals) + '\n'
        text = 'In : h = {:d}'.format(vals[0])
    elif (action == 'sent'):
        # text = 'Sent: ' + str(vals) + '\n'
        text = 'Out: flag = {:d}, x = {:d}, y = {:d}'.format(vals[0],
                                                        vals[1], vals[2])
    elif (action == 'open'):
        text = 'Log-file opened'
    elif (action == 'close'):
        text = 'Log-file closed'
    elif (action == 'connect'):
        text = "Connected to " + vals[0] + ' - ' + vals[1]
    else:
        print('Action unknown')
        return
    print(text)
    btProtocol.write(str(datetime.datetime.now()) + ' ' + text + '\n')
    
def cleanUpConnection():
    # closing the connection explicitly is nice, but also automatic
    btChannel.close()
    
    documentConnection('close', [])
    btProtocol.close()


######################################################################
# Bluetooth with NXT-Python
######################################################################

def findPi(teamName):
    piName = teamName + "pi"
    return findDevice(piName)

