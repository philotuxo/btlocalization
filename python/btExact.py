from PyQt4 import QtGui
import sys, os, time

from lib.btParticle_ui import Ui_btParticle
from lib.histogram_visuals import *
from lib.simulationThread import SimulationFileThread
from lib.bleThread import BluetoothThread
from lib.btQtCore import *
from lib.common import getAdapters
from math import log, exp
import Queue

class ExactImageScene(btImageScene):
    def __init__(self, btViewerGui):
        QtGui.QGraphicsScene.__init__(self)
        # self.circleRadius = 4
        self.originPoint = None
        self.positiveDirLines = [ None, None, None ]
        self.tempCircle = None
        self.btV = btViewerGui
        self.pairs = []
        self.limits = [ None, None ]
        self.frame = [ None, None, None, None ]

    def addProbPoint(self, point, prob):
        newCell = ProbabilityCell(
                    point.x(),
                    point.y(),
                    prob
                    )

        self.addItem(newCell)
        return newCell


class btViewerGui(QtGui.QMainWindow):
    def __init__(self, fQueue, bQueue, outQueue, configFile = None):
        self.qt_app = QtGui.QApplication(sys.argv)
        QtGui.QWidget.__init__(self, None)

        # create the main ui
        self.ui = Ui_btParticle()
        self.ui.setupUi(self)
        self.imageScene = ExactImageScene(self)
        self.pointsSelected = []

        self.colorlines = colorlines
        self.colorlines.reverse()

        self.macColors = {}
        self.dataHist = {}
        self.beacons = None

        # data process
        self.ui.readDataButton.clicked.connect(self.readDataButtonPressed)
        self.listPointItems = {}
        self.listPointItemsRev = {}
        self.listBeaconItems = {}
        self.ui.resetDataButton.clicked.connect(self.resetDataButtonPressed)

        self.ui.pointsAvailable.clicked.connect(self.pointsAvailablePressed)
        self.ui.pointsAvailable.itemSelectionChanged.connect(
            self.pointsAvailablePressed)

        # imageButton
        self.imageFile = None
        self.ui.loadImageButton.clicked.connect(self.loadImagePressed)
        self.ui.resetImageButton.clicked.connect(self.resetImagePressed)

        # parameters
        self.ui.loadParametersButton.clicked.connect(self.loadParametersPressed)

        # calibration
        self.params = {}
        self.params["parity"] = None
        self.params["origin"] = None
        self.params["direction"] = None
        self.params["limits"] = None
        self.ori = None

        # mleRun
        # self.ui.theButton.clicked.connect(self.mleRunPressed)
        # self.ui.loadSampleButton.clicked.connect(self.loadSamplesPressed)

        # timers
        self.pTimer = QtCore.QTimer()
        self.ui.buttonStop.clicked.connect(self.stopHMM)
        self.ui.buttonStart.clicked.connect(self.startHMM)

        self.t = QtCore.QTime()

        # particles
        self.probVisuals = {}
        self.probs = {}

        self.ready = True
        self.trueTraj = []
        self.estiTraj = []

        # thread messaging
        self.fQueue = fQueue
        self.bQueue = bQueue
        self.inQueue = None
        self.outQueue = outQueue
        self.ui.inputComboBox.currentIndexChanged.connect(
            self.inputItemChangedPressed)
        self.obsFile = None

        self.fillInputOptions()

        # config file
        if configFile:
            self.configFile = configFile
            self.configFileCheck()

        # for fps
        self.lastDataTime = []

    def run(self):
        self.show()
        self.qt_app.exec_()

    def configFileCheck(self):
        try:
            with open(self.configFile, 'r') as f:
                config = json.load(f)

                if "map" in config.keys():
                    self.loadImagePressed(config["map"])
                if "par" in config.keys():
                    self.loadParametersPressed(config["par"])
                if "hst" in config.keys():
                    self.readDataButtonPressed(config["hst"])
                print "Config file loaded: " + self.configFile
        except:
            print "Problem with the config File: " + self.configFile

    def resetImagePressed(self):
        self.imageFile = None
        self.updateImage()
        self.ui.noImageLabel.setVisible(True)

    def loadImagePressed(self, imageFile = None):
        if not imageFile:
            imageFile = QtGui.QFileDialog.getOpenFileName(self,
                                                      'Open file',
                                                      './maps',
                                                      'Images (*.png *.xpm '
                                                      '*.jpg)' )
        if not imageFile:
            return
        with open(imageFile, 'r') as f:
            try:
                self.imageFile = imageFile
                # say that an image is loaded
                print "Image loaded: " + imageFile
            except:
                print "Problem with image file: " + self.imageFile
                self.imageFile = None
            finally:
                self.updateImage()

    def fillInputOptions(self):
        self.adapters = []
        self.ui.inputComboBox.addItem("Select an input")
        self.adapters.append(None)
        self.ui.inputComboBox.addItem("File input")
        self.adapters.append(None)

        # get the adapters from the os
        adapters = getAdapters()

        counter = 2
        for adapter in adapters:
            self.adapters.append(adapter[0])
            self.ui.inputComboBox.addItem("%s: %s" % (adapter[0], adapter[1]))
            counter += 1

    def changeQueue(self, type = None):
        if type == "f":
            self.queueType = 'f'
            self.inQueue = self.fQueue
            print "btExact: Queue changed to the file queue."
            return
        if type == "b":
            self.queueType = 'b'
            self.inQueue = self.bQueue
            print "btExact: Queue changed to the ble queue."
            return
        self.inQueue = None

    def inputItemChangedPressed(self):

        self.stopHMM()

        if self.ui.inputComboBox.currentIndex() == 0:
            self.changeQueue()
            # ilki secildi

        if self.ui.inputComboBox.currentIndex() == 1:
            # file input
            self.obsFile = QtGui.QFileDialog.getOpenFileName(self,
                                              'Open file',
                                              './data',
                                              'Data (*.csv *.trk)' )
            if (self.obsFile[-3:] == "csv"):
                # select file Queue
                self.changeQueue("f")
                self.inQueue.put(("SFILE", self.obsFile))

            if (self.obsFile[-3:] == "trk"):
                # select file Queue
                self.changeQueue("f")
                self.inQueue.put(("TFILE", self.obsFile))

        # bluetooth tread
        if self.ui.inputComboBox.currentIndex() > 1:
            # select ble queue
            self.changeQueue("b")
            self.inQueue.put((
                "BDADDR",
                self.adapters[self.ui.inputComboBox.currentIndex()] ))

    def setOpacity(self, opacity):
        newImage = QtGui.QImage(self.frame.size(), QtGui.QImage.Format_ARGB32)
        newImage.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter (newImage)
        painter.setOpacity(opacity)
        painter.drawImage(
                QtCore.QRect(0, 0,
                            self.frame.width(),
                            self.frame.height()),self.frame)

        return newImage

    def updateImage(self):
        # self.clearParticleVisuals()
        self.frame = QtGui.QImage(self.imageFile)
        self.frame = self.setOpacity(0.0)
        self.imageScene.clearParameters()
        self.imageScene.clear()
        self.imageScene.addPixmap(QtGui.QPixmap.fromImage(self.frame))
        self.imageScene.setImageSize(self.frame.size())
        self.imageScene.update()
        self.ui.imageView.setScene(self.imageScene)
        self.putBeacons()
        self.putPoints()
        if self.imageFile:
            # self.imageScene.clearParameters()
            self.imageScene.putParameters()
            self.ui.noImageLabel.setVisible(False)

    def putBeacons(self):
        if self.imageFile and self.beacons:
            # colorize item list
            for mac in self.beacons.keys():
                if mac in self.macColors.keys():
                    color = QtGui.QColor(self.macColors[mac])
                else:
                    color = QtGui.QColor(255,255,255)

                newPoint = real2Pix(self.params, self.beacons[mac])

                self.imageScene.addPoint(newPoint, mac[-5:], color)

    def putPoints(self):
        ptsList = []
        for pair in self.imageScene.pairs:
            if pair[0] not in ptsList:
                ptsList.append(pair[0])
            if pair[1] not in ptsList:
                ptsList.append(pair[1])

        for pts in self.dataHist.keys():
            if pts in self.listPointItems:
                if pts in ptsList:
                    self.imageScene.addPoint(real2Pix(self.params, pts),
                                             "",
#                                                str(pts[0])+","+str(pts[1]),
                                                QtGui.QColor(0,255,0))
                else:
                    if self.listPointItems[pts].isSelected():
                        self.imageScene.addPoint(real2Pix(self.params, pts),
                                             "",
#                                                str(pts[0])+","+str(pts[1]),
                                                QtGui.QColor(0,0,0))
                    else:
                        self.imageScene.addPoint(real2Pix(self.params, pts),
                                             "",
#                                                str(pts[0])+","+str(pts[1]),
                                                QtGui.QColor(255,255,255))
            if pts in self.probs.keys():
                self.probVisuals[pts] = self.imageScene.addProbPoint(
                        real2Pix(self.params, pts),self.probs[pts])

    def updateProbVisuals(self):
        for i in self.probs.keys():
            self.probVisuals[i].updateProb(self.probs[i])

    def updateEstimated(self):
        estimatedVisual = self.imageScene.addPoint(
                real2Pix(self.params, self.estimated) , "",
                QtGui.QColor(0,255,255),
                radius=3)

        if len(self.estiTraj) > 0:
            br = QtGui.QBrush()
            br.setStyle(1)
            br.setColor(QtGui.QColor(0,255,255,64))
            self.estiTraj[-1].setBrush(br)
            self.estiTraj[-1].setPen(QtGui.QPen(QtGui.QColor(0,128,128)))

        self.estiTraj.append(estimatedVisual)
        if len(self.estiTraj) > 10:
            rem = self.estiTraj.pop(0)
            self.imageScene.removeItem(rem)


    def updateProbs(self):
        for key in self.probs.keys():
            self.probs[key] = self.alpha[self.pointer[key],0]

        m = 0
        retKey = None
        for key in self.pointer.keys():
            if self.alpha[self.pointer[key],0] > m:
                m = self.alpha[self.pointer[key],0]
                retKey = key
        self.estimated = retKey


    def addTrajectory(self, point):
        visual = self.imageScene.addPoint(real2Pix(self.params,point),
                                            "",
                                            QtGui.QColor(255,255,0),
                                            radius=3)
        if len(self.trueTraj) > 0:
            br = QtGui.QBrush()
            br.setStyle(1)
            br.setColor(QtGui.QColor(255,255,0,64))
            self.trueTraj[-1][1].setBrush(br)
            self.trueTraj[-1][1].setPen(QtGui.QPen(QtGui.QColor(128,128,0)))

        self.trueTraj.append([point, visual])

        if len(self.trueTraj) > 10:
            a,rem = self.trueTraj.pop(0)
            self.imageScene.removeItem(rem)

    def loadParametersPressed(self, parFile = None):
        if not parFile:
            parFile = QtGui.QFileDialog.getOpenFileName(self,
                                                  'Open file',
                                                  './conf',
                                                  'Parameters (*.par)')

        if not parFile:
            return
        try:
            with open(parFile, 'r') as f:
                tempParams = json.load(f)
                tempParams["origin"] = QtCore.QPoint(tempParams["origin"][0],
                                                     tempParams["origin"][1])
                tempParams["direction"] = QtCore.QPoint(tempParams["direction"][0],
                                                       tempParams["direction"][1])
                tempParams["limits"] = ( (tempParams["limits"][0],
                                          tempParams["limits"][1]),
                                         (tempParams["limits"][2],
                                          tempParams["limits"][3]))
                self.params = tempParams
                print "Parameters loaded: " + parFile
        except:
            print "Incompatible File: " + parFile
        finally:
            self.updateImage()

    def readDataButtonPressed(self, dataFile):
        if not dataFile:
            self.dataFile = QtGui.QFileDialog.getOpenFileName(self,
                                                      'Open file',
                                                      './data',
                                                      'Hst File ('
                                                      '*.hst)')
        else:
            self.dataFile = dataFile

        if not self.dataFile:
            return

        # progress dialog patch
        self.dataHist, self.bins, self.beacons, self.macColors = \
            parse_hst_file(self.dataFile)


        for point in self.dataHist.keys():
            if point not in self.probs.keys():
                self.probs[point] = 1.0/len(self.dataHist)

        print "Histograms loaded: " + self.dataFile

        self.resetLists()

    def resetLists(self):
        if len(self.dataHist) > 0:
            if self.imageFile:
                self.updateImage()
        if self.dataFile:
            # set points
            self.ui.dataFile.setText(
                "File: %s" % (str(os.path.basename(str(self.dataFile)))))
            self.updatePointList()

    def updatePointList(self):
        self.ui.pointsAvailable.clear()
        self.listPointItems.clear()
        for point in self.dataHist.keys():
            # fast conversion update patch
            itemPoint = QtGui.QListWidgetItem("%s,%s" %
                                              (point[0], point[1]))
            self.ui.pointsAvailable.addItem(itemPoint)

            self.listPointItems[point] = itemPoint
            self.listPointItemsRev[itemPoint] = point

    def updateDataShow(self, mac, rssi, txValue):
        now = time.time()
        n = len(self.lastDataTime)
        # if not n == 0:

        if  n > 5:
            self.lastDataTime.pop(0)
        self.lastDataTime.append(now)
        diff = now - self.lastDataTime[0]
        # self.lastDataTime = now
        if diff:
            self.ui.dps.setText("DPS: %s hz" % round(float(n)/diff,1))

        if self.ui.collectDataShow.count() > 6:
            self.ui.collectDataShow.takeItem(0)
        temp = QtGui.QListWidgetItem(str(mac) +
                                     " | " + str(rssi) +
                                     " | " + str(txValue))
        if mac in self.macColors.keys():
            temp.setTextColor(QtGui.QColor(self.macColors[mac]))
        self.ui.collectDataShow.addItem(temp)

    def pointsAvailablePressed(self):
        self.pointsSelected = []
        itemBeacon = None
        beaconsBefore = []
        for beacon in self.ui.beaconsAvailable.selectedItems():
            beaconsBefore.append(str(beacon.text()[0:17]))

        if len(self.ui.pointsAvailable.selectedItems()) > 0:
            for i in self.ui.pointsAvailable.selectedItems():
                if i in self.listPointItemsRev.keys():
                    self.pointsSelected.append(self.listPointItemsRev[i])
            beacons = {}
            for point in self.pointsSelected:
                for b in self.dataHist[point]:
                    if b not in beacons.keys():
                        beacons[b] = []
                    beacons[b].append(point)

            self.ui.beaconsAvailable.clear()
            self.listBeaconItems.clear()
            for mac in beacons.keys():
                if len(beacons[mac]) > 1:
                    itemBeacon = QtGui.QListWidgetItem("%s (%s)" % (
                            mac.strip(), len(beacons[mac])))
                    itemBeacon.setTextColor(QtGui.QColor(self.macColors[mac]))
                    self.ui.beaconsAvailable.addItem(itemBeacon)
                    self.listBeaconItems[mac] = itemBeacon
                else:
                    itemBeacon = QtGui.QListWidgetItem("%s" % mac.strip())
                    itemBeacon.setTextColor(QtGui.QColor(self.macColors[mac]))
                    self.ui.beaconsAvailable.addItem(itemBeacon)
                    self.listBeaconItems[mac] = itemBeacon
                if mac in beaconsBefore:
                    if itemBeacon:
                        itemBeacon.setSelected(True)

        else:
            self.ui.beaconsAvailable.clear()
            self.listBeaconItems.clear()

        if self.imageFile and len(self.dataHist) > 0:
            self.updateImage()

    def resetDataButtonPressed(self):
        self.dataHist.clear()
        self.ui.pointsAvailable.clear()
        self.ui.beaconsAvailable.clear()
        self.listPointItems.clear()
        self.listPointItemsRev.clear()

    def startHMM(self):
        if self.inQueue:
            self.inQueue.put(( "START", None ))

        # yeni particle listesi olustur
        if self.params["limits"]:

            self.hmm_initialize()

            # timer baslat
            self.pTimer.start(1)
            self.pTimer.timeout.connect(self.hmm_single_step)

            # tracking icin
            self.orient = 0
            self.dist = 0


    def stopHMM(self):
        # timer durdurulacak
        self.pTimer.stop()
        if self.inQueue:
            self.inQueue.put(( "END", None ))

    def hmm_single_step(self):
        # get the new data from the queue
        if self.outQueue.qsize() > 0:
            # get new observation
            message = self.outQueue.get()
            if self.queueType == 'f':
                timeStamp = message[0]
                beacon = message[1]
                rssi = message[2]
                dist = message[3]
                orientDelta = message[4]
                acc= message[5]
                point = message[6]

                self.addTrajectory(point)

            # if this is live beacon data
            if self.queueType == 'b':
                timeStamp = round(message[0] - self.timeStart,2)
                beacon = message[1]
                rssi = message[2]
                point = None

                # print beacon, rssi
            self.updateDataShow(beacon, rssi, timeStamp)

            # print self.logAlpha
            # print self.logAlphaPredict

            if not self.ready:
                return
            self.ready = False
            if beacon not in self.beacons:
                print "HMM: Unknown beacon: " + beacon
                return

            self.hmm_predict()
            self.hmm_update(beacon,rssi)
            self.hmm_normalize_exp()
            self.updateProbs()
            self.updateProbVisuals()
            self.updateEstimated()

            self.ready = True
        else:
            time.sleep(.001)

    def hmm_initialize(self):
        self.N = len(self.dataHist.keys())
        self.pointer = {}
        self.logAlpha = np.matrix(np.ones([self.N,1])) * np.log(1.0/self.N)
        self.logAlphaPredict = np.matrix(np.zeros([self.N,1]))

        self.hmm_create_index()
        self.hmm_get_transition()

    def hmm_create_index(self):
        counter = 0
        for key in self.dataHist.keys():
            self.pointer[key] = counter
            counter += 1

    def hmm_get_transition(self):
        self.A = np.matrix(np.zeros([self.N, self.N]))

        for key in self.dataHist.keys():
            closest = find_closest_points(key,self.dataHist.keys(),numMax=8)
            for keyNext in self.dataHist.keys():
                if key == keyNext:
                    self.A[self.pointer[key], self.pointer[keyNext]] = .75
                if keyNext in closest :
                    self.A[self.pointer[key], self.pointer[keyNext]] = .25/(
                        len(closest))
                else:
                    self.A[self.pointer[key], self.pointer[keyNext]] = 0

    def hmm_update(self, beacon, rssi):
        for key in self.pointer.keys():
            self.logAlpha[self.pointer[key],0] = \
                np.log(self.dataHist[key][beacon][rssi - rssi_start]) + \
                self.logAlphaPredict[self.pointer[key],0]

    def hmm_predict(self):
        # stable computation
        mx = max(self.logAlpha)
        p = np.exp(self.logAlpha - mx)
        self.logAlphaPredict = np.log(self.A * p) + mx

    def hmm_normalize_exp(self):
        mx = max(self.logAlpha)
        EXP = np.exp(self.logAlpha - mx)
        self.alpha = EXP / sum(EXP)

def main():

    bQueue = Queue.Queue()
    fQueue = Queue.Queue()
    outQueue = Queue.Queue()
    sThread = SimulationFileThread("FileThread", fQueue, outQueue)
    bThread = BluetoothThread("BluetoothThread", bQueue, outQueue)

    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    else:
        configFile = None

    sThread.start()
    bThread.start()
    app = btViewerGui(fQueue, bQueue, outQueue, configFile)
    app.run()

    # end the threads gracefully
    bQueue.put(["QUIT", None ] )
    fQueue.put(["QUIT", None ] )
    sThread.join()
    bThread.join()

if __name__ == '__main__':
    main()

