# test BLE Scanning software
# jcs 6/8/2014

import blescan
import sys
import bluetooth._bluetooth as bluez
import dbus

# print("Available devices %s" % (str(blescan.getAdapters())))
bdaddr = '00:15:83:E5:B2:69'

dev_id = bluez.hci_devid(bdaddr)
sock = bluez.hci_open_dev(dev_id)
blescan.hci_le_set_scan_parameters(sock)
blescan.hci_enable_le_scan(sock)

while True:
    returnedList = blescan.parse_events(sock, 1)
    print "----------"
    for beacon in returnedList:
        print beacon