import btConnect
import time

start_time = time.time()

teamName = 'Team65'
addr = btConnect.findDevice(teamName)
btConnect.initConnection(addr, teamName)

# need while loop since bluetooth blocks everything once engaged
errorFlag = [0]
print('Listening for message')
while (errorFlag[0] == 0):
    errorFlag = btConnect.btRead()

print(errorFlag)

input("Press enter to begin writing...") # allow for computer to begin reading before write
btConnect.btWrite(3, 1, 0)

# test multiple request ability
print('Listening for message')
errorFlag = [0]
while (errorFlag[0] == 0):
    errorFlag = btConnect.btRead()
print(errorFlag)

x = input('Wait1') # otherwise too fast and NXT still clears messages

input("Press enter to begin writing...") # allow for computer to begin reading before write
btConnect.btWrite(-3, 1, -3)

btConnect.cleanUpConnection()

print("--- %s seconds ---" % (time.time() - start_time))
