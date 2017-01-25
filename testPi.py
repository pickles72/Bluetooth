# TO USE TESTING PROGRAMS, MUST HAVE testPi.py AND testBT.py
#
#   1. Change RaspberryPi name to Team65pi
#   2. Place file gpsName.txt in folder with btStudent.txt
#   3. Place the name of the computer being connected to
#   3a. Alternately, use get MAC to provide MAC address of the GPS computer.
#   4. Pair the pi and the computer
#   5. Start testBT.py on the computer (python3 testBT.py)
#   6. Start testPi.py on the pi (python3 testPi.py)
#   7. Check for proper output
#
#   ORDER
#   1. Connect
#   2. Write
#   3. Read
#   4. Write
#   5. Read
#   6. Close connection
#
# Author: Peter Jones
# Date  : Spring 2017

import btStudent
import time

print("Running Tests...")

# Test of loading file with computer name
print("Testing ability to load computer name from file")
btStudent.findGPS()
print("GPS name found: " + btStudent.deviceName)
time.sleep(2)

# Test connection ability
print("Testing Connection...")
btStudent.initConnection()

if btStudent.btSocket is None:
    print("Connection failed")
else:
    print("Connection successful")

# Test write ability
input("Press enter to begin writing...") # allow for computer to begin reading before write
print("Testing write...")
time.sleep(1)
btStudent.btWrite(3, 2, 1)
input("Press enter to continue...")

# Test read ability
errorFlag = [0]
print('Listening for message')
while (errorFlag[0] == 0):
    errorFlag = btStudent.btRead()
print(errorFlag)
time.sleep(2)

# Test write ability
print("Testing write...")
time.sleep(1)
btStudent.btWrite(1, 2, 3)
input("Press enter to continue...")

# Test read ability
errorFlag = [0]
print('Listening for message')
while (errorFlag[0] == 0):
    errorFlag = btStudent.btRead()
print(errorFlag)
time.sleep(2)


print("Testing complete")
btStudent.closeConnection()