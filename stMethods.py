# Author: Peter Jones
# Date  : Spring 2017

import btStudent
import time

def sendMessage(height):
    if btStudent.btSocket is None:
        print("Error! No Connection is Found")
        time.sleep(2)
        return

    btStudent.btWrite(0x00, height, 0x00)