from ast import literal_eval

__author__ = 'serhan'
import threading
import time

class SimulationFileThread (threading.Thread):
    def __init__(self, name, inQueue, outQueue, logQueue = None, realTime =
    True):
        threading.Thread.__init__(self)
        self.name = name
        self.inQueue = inQueue
        self.outQueue = outQueue # the queue to put sample data
        self.dataFile = None
        self.running = False
        self.lQueue = logQueue
        self.rtp = realTime

    def readStationaryFile(self):
        self.data = []
        with open(self.dataFile, 'r') as f:
            # readfile
            for line in f:
                each = line.split(',')
                time = float(each[0])
                rssi = int(each[5])
                mac = each[4].strip()

                self.data.append((time, mac, rssi))

            if f:
                if self.lQueue:
                    self.lQueue.put(self.name + ": Data file loaded "+ \
                                              self.dataFile)
                else:
                    print self.name + ": Data file loaded "+ self.dataFile
            else:
                if self.lQueue:
                    self.lQueue.put(": Incompatible data file: " + self.dataFile)
                else:
                    print ": Incompatible data file: " + self.dataFile
                self.dataFile = None


    def readTrackingFile(self):
        self.data = []
        with open(self.dataFile, 'r') as f:
            # readfile
            for line in f:
                each = literal_eval(line.strip())
                time = float(each[0])
                rssi = int(each[8])
                mac = each[7].strip()
                point = each[1]
                acc = each[6]
                dist = each[2]
                orientDelta = each[3]

                self.data.append(
                        (time,
                         mac,
                         rssi,
                         dist,
                         orientDelta,
                         acc,
                         point))

            if f:
                if self.lQueue:
                    self.lQueue.put(self.name + ": Data file loaded "+ \
                                              self.dataFile)
                else:
                    print self.name + ": Data file loaded "+ self.dataFile
            else:
                if self.lQueue:
                    self.lQueue.put(self.name + ": Incompatible data file: " + \
                                      self.dataFile)
                else:
                    print self.name + ": Incompatible data file: " + self.dataFile
                self.dataFile = None

    def run(self):
        if self.lQueue:
            self.lQueue.put(self.name + ": Starting.")
        else:
            print self.name + ": Starting."

        while(True):
            # receive message
            if self.inQueue.qsize() > 0:
                message = self.inQueue.get()
                if self.lQueue:
                    self.lQueue.put(self.name + ": Message Recieved: " +
                                    str(message))
                else:
                    print self.name + ": Message Recieved: " + str(message)

                if message[0] == "QUIT":
                    if self.lQueue:
                        self.lQueue.put(self.name + ": Quitting.")
                    else:
                        print self.name + ": Quitting."
                    self.running = False
                    break
                if message[0] == "END":
                    if self.lQueue:
                        self.lQueue.put(self.name + ": Stopping.")
                    else:
                        print self.name + ": Stopping."
                    self.running = False
                if message[0] == "SFILE":
                    self.dataFile = message[1]
                    if self.lQueue:
                        self.lQueue.put(self.name + ": Loading file " + self.dataFile)
                    else:
                        print self.name + ": Loading file " + self.dataFile
                    self.readStationaryFile()
                    self.running = False
                if message[0] == "TFILE":
                    self.dataFile = message[1]
                    if self.lQueue:
                        self.lQueue.put(self.name + ": Loading file " + self.dataFile)
                    else:
                        print self.name + ": Loading file " + self.dataFile
                    self.readTrackingFile()
                    self.running = False
                if message[0] == "START":
                    if self.lQueue:
                        self.lQueue.put(self.name + ": Starting simulation.")
                    else:
                        print self.name + ": Starting simulation."
                    self.running = True
                    counter = 0

            if not self.running:
                time.sleep(.05)
                continue

            curTime = self.data[counter][0]
            self.outQueue.put(self.data[counter])

            if counter + 1 == len(self.data):
                self.outQueue.put("EOF")
                if self.lQueue:
                    self.lQueue.put(self.name + ": End of sample file")
                else:
                    print self.name + ": End of sample file"
                self.running = False
                counter = 0
                continue
            nextTime = self.data[counter + 1][0]
            counter += 1

            # wait for the time being
            if self.rtp:
                time.sleep(nextTime-curTime)

        if self.lQueue:
            self.lQueue.put(self.name + ": Ending.")
        else:
            print self.name + ": Ending."
