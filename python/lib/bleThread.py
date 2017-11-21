__author__ = 'serhan'

import threading
import time, sys
from blescan.blescan import *

class BluetoothThread (threading.Thread):
    def __init__(self, name, inQueue, outQueue, logQueue = None):
        threading.Thread.__init__(self)
        self.name = name
        self.inQueue = inQueue
        self.outQueue = outQueue
        self.saveFID = None
        self.point = None
        self.bdaddr = None
        self.sock = None
        self.sending = False
        self.selectedMAC = None
        self.lQueue = logQueue

    def setDevice(self, bdaddr):
        # initialize device
        dev_id = bluez.hci_devid(bdaddr)
        try:
            self.sock = bluez.hci_open_dev(dev_id)
            hci_le_set_scan_parameters(self.sock)
            hci_enable_le_scan(self.sock)
            if self.lQueue:
                self.lQueue.put(self.name + ": Device ready - " + bdaddr)
            else:
                print self.name + ": Device ready - " + bdaddr
        except:
            if self.lQueue:
                self.lQueue.put(self.name + ": Error accessing bluetooth " \
                  "device. Check permissions.")
            else:
                print self.name + ": Error accessing bluetooth " \
                  "device. Check permissions."
            self.bdaddr = None
            self.sock.close()
            self.sock = None

    def incoming_parser(self, message):
        if message[0] == "BDADDR":
            if message[1] == None:
                self.bdaddr = None
                if self.sock:
                    self.sock.close()
                    self.sock = None
            else:
                self.bdaddr = str(message[1])
                self.setDevice(self.bdaddr)
                if self.lQueue:
                    self.lQueue.put(self.name + ": Setting bdaddr to " + \
                      str(self.bdaddr))
                else:
                    print self.name + ": Setting bdaddr to " + \
                      str(self.bdaddr)
                return False

        if message[0] == "START":
            self.selectedMAC = message[1]
            if self.sock:
                if self.lQueue:
                    self.lQueue.put(self.name + ": Starting sending data.")
                else:
                    print self.name + ": Starting sending data. "
                self.sending = True
            return False

        if message[0] == "END":
            self.sending = False
            self.selectedMAC = None
            if self.lQueue:
                self.lQueue.put(self.name + ": Stopping sending data. ")
            else:
                print self.name + ": Stopping sending data. "
            return False

        if message[0] == "FILE":
            if message[1] == None:
                # close the file
                self.saveFID.close()
            else:
                # open a file
                self.saveFID = open(message[2], 'a+')
                self.imageFile = message[1]
                self.point = (message[3], message[4])
            return False

        if message[0] == "QUIT":
            if self.sock:
                self.sock.close()
            return True


    def run(self):
        if self.lQueue:
            self.lQueue.put(self.name + ": Starting.")
        else:
            print self.name + ": Starting."
        while(True):
            if self.inQueue.qsize() > 0:
                # if this thread hears anything
                message = self.inQueue.get()
                if self.lQueue:
                    self.lQueue.put(self.name + ": Message Recieved:", message)
                else:
                    print self.name + ": Message Recieved:", message

                if self.incoming_parser(message):
                    break
            else:
                if self.sock:
                    returnedList = parse_events(self.sock, 1)

                    # put into the queue
            # queue format:
                    for beacon in returnedList:
                        if self.sending:
                            if not self.selectedMAC or (
                                self.selectedMAC
                                    and beacon[0] in self.selectedMAC):
                                self.outQueue.put((
                                    beacon[6], # timeStamp
                                    beacon[0], # mac
                                    beacon[5][0], # rssi
                                    beacon[1], # uuid
                                    beacon[2], # major
                                    beacon[3], # minor
                                    beacon[4][0] # txValue
                                ))

                        # save to file
                        if self.saveFID and not self.saveFID.closed:
            # file format : time,imageFile,point,beaconMAC, RSSI, txValue
                            if self.selectedMAC == None:
                                continue
                            if beacon[0] in self.selectedMAC:
                                self.saveFID.write(str(beacon[6]) + ", " +
                                      str(self.imageFile) + ", " +
                                      str(self.point[0]) + ", " +
                                      str(self.point[1]) + ", " +
                                      str(beacon[0]) + ", " +
                                      str(beacon[5][0]) + ", " +
                                      str(beacon[4][0]) + '\n')
                                self.saveFID.flush()
                else:
                    time.sleep(.000001) # 1 microsecond if possible

        if self.lQueue:
            self.lQueue.put(self.name + ": Quitting.")
        else:
            print self.name + ": Quitting."
