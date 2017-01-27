# Bluetooth communication files to help RaspberryPi
# mimic the nxt brick communication methods
# authors: Peter Jones, Michael Fruhnert
# date: Fall 2016

import bluetooth
import time

# Give laptop device name to be put into gpsName.txt file so that it does not need
# to be reentered every time the program is restarted by the student
filename = "gpsName.txt" # name of file containing GPS device name
deviceList = None # list of devices found
gpsAddr = None # stores MAC Address of GPS
btSocket = None # stores Bluetooth connection
dataTot = b'' # stores bytes received
deviceName = None


######################################################################
# Bluetooth Connection Methods
######################################################################

def initConnection():
    global gpsAddr, btSocket
    port = 1

    # Find GPS MAC address
    # Attempt twice
    if gpsAddr == None:
        findGPS()
    if gpsAddr == None:
        print("Error: Failure to connect, GPS device not found")
        return

    try:
        btSocket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        btSocket.connect((gpsAddr, port))
        btSocket.settimeout(1)  # 1 seconds of reading (minimum)
    except bluetooth.btcommon.BluetoothError as err:
        # Error handling
        print('Error occured while using socket')
        return


# Function to find device MAC Address
def findGPS():
    global filename, deviceList, gpsAddr, deviceName

    i=0
    while(i<3):
        try:
            # Read device name from file
            file = open(filename)
            line = file.readline()
            deviceName = line.strip()
            if deviceName == None:
                # Error handling
                print("No device name in file " + filename)
                return None
        except IOError:
            print("Error! Faiure to open device name file. Attempt #" + str(i+1))
            time.sleep(1)
        i += 1


    i = 0
    while i < 3:
        deviceList = bluetooth.discover_devices()

        for device in deviceList:
            if deviceName == bluetooth.lookup_name(device):
                gpsAddr = device
                return device

        time.sleep(1)
        i+=1

    return None


def closeConnection():
    global btSocket

    btSocket.close()


def setMAC():
    global gpsAddr

    while True:
        gpsAddr = input("Please enter device MAC address: (xx:xx:xx:xx)")

        if len(gpsAddr) != 11:
            print("Please enter valid MAC address")
        else:
            return

def printDevices():
    deviceList = bluetooth.discover_devices()

    for device in deviceList:
        print(device)
        if bluetooth.lookup_name(device) != None:
            print(bluetooth.lookup_name(device))

    return



######################################################################
# Message Methods
######################################################################


def btWrite(err, xCoor, yCoor):
    vals = [err, xCoor, yCoor]
    # Code possibly outdated see OneNote note
    code = b'\x0A\x00\x80\x09\x00\x06' # same metadata (see comment above)
    for i in vals:
        code += i.to_bytes(2, byteorder = 'little', signed = True)
    btSocket.send(code)

    return code

def btRead():
    global dataTot
    while True:
        if (len(dataTot) < 12):
            try:
                # generally one recv should not work => use a loop
                # However, message seems to be small enough
                data = btSocket.recv(50) # size of buffer (12 Byte message)
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
                return val
            else:
                dataTot.pop(0) # for all unknown message types
