import sys, os, time
from lib.btParticle_ui import Ui_btParticle
from lib.histogram_visuals import *
from lib.simulationThread import SimulationFileThread
from lib.bleThread import BluetoothThread
from lib.common import getAdapters
from lib.btQtCore import *
import Queue
from multiprocessing import Queue as mQueue
from multiprocessing import Process

numProcess = 4

def processFunction(name, pQueue, doneQueue):
    cumul = None
    best = None
    print "Starting Process-" + name
    while True:
        if pQueue.qsize() > 0:
            data = pQueue.get()
            if data == "QUIT":
                print "Ending Process-" + name
                break
            if data[0] == 'r':
                cumul = None
                best = None

            if data[0] == 'c':
                cumul = data[1]
            if data[0] == 'b':
                best = data[1]
            if data[0] == 's':
                newIndex = randgen(cumul, data[1], best)
                doneQueue.put(newIndex)
        else:
            time.sleep(.0001)


class ParticleImageScene(btImageScene):
    def mousePressEvent(self, event):
        self.latestPoint = QtCore.QPoint(
                event.scenePos().x(), event.scenePos().y())
        self.btV.togglePressed(self.latestPoint)

class btViewerGui(QtGui.QMainWindow):
    def __init__(self, fQueue, bQueue, outQueue, pQueues, doneQueue,
                 configFile = None,
                 trackFile = None):
        self.qt_app = QtGui.QApplication(sys.argv)
        QtGui.QWidget.__init__(self, None)

        # create the main ui
        self.ui = Ui_btParticle()
        self.ui.setupUi(self)
        self.imageScene = ParticleImageScene(self)
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

        # grid File
        self.gridFile = None

        # timers
        self.pTimer = QtCore.QTimer()
        self.ui.buttonStop.clicked.connect(self.stopParticleFilter)
        self.ui.buttonStart.clicked.connect(self.startParticleFilter)

        self.t = QtCore.QTime()

        # particles
        self.sizeParticles = 10000
        self.sizeParticleVisuals = 100
        self.sizeBestWeights = self.sizeParticles
        self.transitionType = 1 # 0:diffusion, 1:odometry, 2:accelerometer
        self.flush = False
        self.pf_likelihood = self.pf_likelihood_closest

        self.particles = None
        self.particlesHat = None
        self.particleWeights = None
        self.particleWeightedMean = None
        self.ready = True
        self.trueTraj = []
        self.estiTraj = []

        self.weights_sum = 0

        # process messaging
        self.pQueues = pQueues
        self.doneQueue = doneQueue

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

        self.pointsAvailablePressed()

        if trackFile:
            self.obsFile = trackFile
            self.selectFile()
            self.transitionType = 1
            self.startParticleFilter()

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
                if "grd" in config.keys():
                    self.gridFile = config["grd"]
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
                                                      '../maps',
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
        self.ui.inputComboBox.addItem("Input file: Diffusion")
        self.ui.inputComboBox.addItem("Input file: Odometry")
        self.ui.inputComboBox.addItem("Input file: Accelerometer")

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
            print "btParticle: Queue changed to the file queue."
            return
        if type == "b":
            self.queueType = 'b'
            self.inQueue = self.bQueue
            print "btParticle: Queue changed to the ble queue."
            return
        self.inQueue = None

    def selectFile(self):
        if (self.obsFile[-3:] == "csv"):
            # select file Queue
            self.changeQueue("f")
            self.inQueue.put(("SFILE", self.obsFile))

        if (self.obsFile[-3:] == "trk"):
            # select file Queue
            self.changeQueue("f")
            self.inQueue.put(("TFILE", self.obsFile))

    def inputItemChangedPressed(self):

        self.stopParticleFilter()

        if self.ui.inputComboBox.currentIndex() == 0:
            self.changeQueue()
            # ilki secildi

        if self.ui.inputComboBox.currentIndex() in range(1,4):
            # file input
            self.obsFile = QtGui.QFileDialog.getOpenFileName(self,
                                              'Open file',
                                              '../data',
                                              'Data (*.csv *.trk)' )

            self.selectFile()

            self.transitionType = self.ui.inputComboBox.currentIndex()-1

        # bluetooth thread
        if self.ui.inputComboBox.currentIndex() > 3:
            # select ble queue
            self.changeQueue("b")
            self.inQueue.put((
                "BDADDR",
                self.adapters[self.ui.inputComboBox.currentIndex()-4] ))


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
        self.clearParticleVisuals()
        self.frame = QtGui.QImage(self.imageFile)
        self.frame = self.setOpacity(0.1)
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

    def updateParticleVisuals(self):
        self.clearParticleVisuals()
        self.putParticles()

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
                                                QtGui.QColor(0,255,0,100))
                else:
                    if self.listPointItems[pts].isSelected():
                        self.imageScene.addPoint(real2Pix(self.params, pts),
                                             "",
#                                                str(pts[0])+","+str(pts[1]),
                                                QtGui.QColor(0,0,0,75))
                    else:
                        self.imageScene.addPoint(real2Pix(self.params, pts),
                                             "",
#                                                str(pts[0])+","+str(pts[1]),
                                                QtGui.QColor(100,100,255,25))
    def addTrajectory(self, point):
        visual = self.imageScene.addPoint(real2Pix(self.params,point),
                                            "",
                                            QtGui.QColor(255,255,0),
                                            pencolor= QtGui.QColor(128,128,0),
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


    def putParticles(self):
        if not self.particles:
            return
        for i in range(self.sizeParticleVisuals):
            if self.bestWeights[i]:

                # lhColor = int(255.0 * i/self.sizeParticleVisuals)
                # print lhColor, self.particleWeights[sorting[i]]
                lhColor = 200
                # visualize the evaluation
                point = real2Pix(
                        self.params, self.particlesHat[self.bestIndexes[i]][0])
                self.particleVisuals[i] = self.imageScene.addPoint(
                    point, "",QtGui.QColor(lhColor, lhColor, lhColor),
                        radius=2
                )

        estimated = self.imageScene.addPoint(
                real2Pix(self.params, self.particleWeightedMean)
                , "",
                QtGui.QColor(0,255,255),
                pencolor=QtGui.QColor(0,128,128),
                radius=3)

        if len(self.estiTraj) > 0:
            br = QtGui.QBrush()
            br.setStyle(1)
            br.setColor(QtGui.QColor(0,255,255,64))
            self.estiTraj[-1].setBrush(br)
            self.estiTraj[-1].setPen(QtGui.QPen(QtGui.QColor(0,128,128)))

        self.estiTraj.append(estimated)
        if len(self.estiTraj) > 10:
            rem = self.estiTraj.pop(0)
            self.imageScene.removeItem(rem)

    def loadParametersPressed(self, parFile = None):
        if not parFile:
            parFile = QtGui.QFileDialog.getOpenFileName(self,
                                                  'Open file',
                                                  '../conf',
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
                                                      '../data',
                                                      'Hst File ('
                                                      '*.hst)')
        else:
            self.dataFile = dataFile

        if not self.dataFile:
            return

        # progress dialog patch
        self.dataHist, self.bins, self.beacons, self.macColors = \
            parse_hst_file(self.dataFile)


        # for mac in dataColors.keys():
        #     self.macColors[mac] = QtGui.QColor(dataColors[mac][0],
        #                                        dataColors[mac][1],
        #                                        dataColors[mac][2])

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

    def updateDataShow(self, mac, rssi, timeStamp):
        n = len(self.lastDataTime)
        # if not n == 0:

        if  n > 5:
            self.lastDataTime.pop(0)
        self.lastDataTime.append(timeStamp)
        diff = timeStamp - self.lastDataTime[0]
        # self.lastDataTime = now
        if diff:
            self.ui.dps.setText("DPS: %s hz" % round(float(n)/diff,1))

        if self.ui.collectDataShow.count() > 6:
            self.ui.collectDataShow.takeItem(0)
        temp = QtGui.QListWidgetItem(str(mac) +
                                     " | " + str(rssi) +
                                     " | " + str(timeStamp))
        if mac in self.macColors.keys():
            temp.setTextColor(QtGui.QColor(self.macColors[mac]))
        self.ui.collectDataShow.addItem(temp)
        self.ui.collectDataShow.update()

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

    def togglePressed(self, point):
        realPoint = pix2Real(self.params, point)
        closest = find_closest_points(
                realPoint,self.dataHist.keys(),2.0, numMax=1)

        if closest[0] in self.pointsSelected:
            self.listPointItems[closest[0]].setSelected(False)
            self.pointsAvailablePressed()
        else:
            self.listPointItems[closest[0]].setSelected(True)
            self.pointsAvailablePressed()

    def resetDataButtonPressed(self):
        self.dataHist.clear()
        self.ui.pointsAvailable.clear()
        self.ui.beaconsAvailable.clear()
        self.listPointItems.clear()
        self.listPointItemsRev.clear()

    def startParticleFilter(self):
        self.error = 0
        self.count = 0
        # prepare grids before receiving data
        if self.pf_likelihood == self.pf_likelihood_grids:
            if self.gridFile:
                print "ParticleFilter: Reading grids."
                self.read_grids()
                print "ParticleFilter: Acquired grids."
            else:
                print "ParticleFilter: Preparing grids with size " + str(self.sizeGrid)
                self.prepare_grids()
                print "ParticleFilter: Prepared grids."


        # yeni particle listesi olustur
        if self.params["limits"]:
            # create the sample base
            self.particleVisuals = [None] * self.sizeParticleVisuals
            self.particleMeanVisual = None

            if self.transitionType == 0: # diffusion
                # state vector: (x,y)
                self.particles = [None] * self.sizeParticles
                self.particlesHat = [None] * self.sizeParticles

            if self.transitionType == 1: # odometry
                # state vector: ((x,y),theta)
                self.particles = [None] * self.sizeParticles
                self.particlesHat = [None] * self.sizeParticles

            if self.transitionType == 2: # acceleration
                # state vector: ((x,y),(x',y'),(x'',y''))
                self.previousTimeStamp = 0
                self.particles = [None] * self.sizeParticles
                self.particlesHat = [None] * self.sizeParticles

            self.particleWeights = [0] * self.sizeParticles
            self.bestWeights = [0] * self.sizeBestWeights
            self.bestIndexes = [0] * self.sizeBestWeights

            # timer baslat
            self.pTimer.start(.5)
            self.timeStart = time.time()
            self.pTimer.timeout.connect(self.pf_single_step)

        # send the start signal
        if self.inQueue:
            self.selectFile()
            self.inQueue.put(( "START", None ))

    def stopParticleFilter(self):
        # timer durdurulacak
        self.pTimer.stop()
        if self.inQueue:
            self.inQueue.put(( "STOP", None ))

    def clearParticleVisuals(self):
        if self.particles == None:
            return
        for i in range(self.sizeParticleVisuals):
            if self.particleVisuals[i]:
                self.imageScene.removeItem(self.particleVisuals[i])
                self.particleVisuals[i] = None

    def pf_single_step(self):
        # get the new data from the queue
        if self.outQueue.qsize() > 0:
            # get new observation
            message = self.outQueue.get()
            if message == "EOF":
                print "Average Error = " + str(self.error / self.count)
                print "with " + str(self.count) + " data points."
                self.stopParticleFilter()
                return

            # if this is the file simulation
            if self.queueType == 'f':
                timeStamp = message[0]
                beacon = message[1]
                rssi = message[2]
                dist = message[3]
                orientDelta = message[4]
                acc= message[5]
                point = message[6]

            # if this is the live beacon data
            if self.queueType == 'b':
                timeStamp = round(message[0] - self.timeStart,2)
                beacon = message[1]
                rssi = message[2]
                point = None

                # print beacon, rssi

            if self.particles[0] == None:
                print "ParticleFilter: Randomly initializing particles"
                self.pf_initialize()

            # don't continue if the beacon does not exist
            if not beacon in self.beacons:
                return

            # don't continue if this function is still running
            if not self.ready:
                return

            self.updateDataShow(beacon, rssi, timeStamp)

            self.ready = False

            # inifialize if the particles are empty
            # evaluate for the weights
            self.t.restart()
            if self.transitionType == 0:
                self.pf_importance_sampling_diffusion(beacon,rssi)
            if self.transitionType == 1:
                self.pf_importance_sampling_odometry(
                        beacon, rssi, dist, orientDelta)
            if self.transitionType == 2:
                self.pf_importance_sampling_acceleration(
                    beacon,
                    rssi,
                    acc,
                    timeStamp - self.previousTimeStamp
                )
                # keep the old time if we're going to process
                self.previousTimeStamp = timeStamp

            self.pf_mean_point()
            # print "IS:", self.t.elapsed()

            self.t.restart()
            self.pf_selectParticlesPar()
            # print "SP:", self.t.elapsed()

            self.t.restart()
            self.updateParticleVisuals()
            if point:
                self.addTrajectory(point)
            # print "VI:", self.t.elapsed()

            err = point_euclid((point[0], point[1]), self.particleWeightedMean)
            self.error += err
            self.count += 1
            print "ER:", self.count, err



            # flush the queue
            if self.flush:
                while self.outQueue.qsize() > 0:
                    flu = self.outQueue.get()
            # we are finished
            self.ready = True
        # else:
        #     time.sleep(.0000001)

    def pf_initialize(self):
        # N tane particle at
        if self.transitionType == 0:
            for i in range(self.sizeParticles):
                point = sampleRandomPoint2dUniform(self.params["limits"])
                self.particles[i] = [point]

        if self.transitionType == 1:
            for i in range(self.sizeParticles):
                orient = random.random() * math.pi
                point = sampleRandomPoint2dUniform(self.params["limits"])
                self.particles[i] = [point, orient]

        if self.transitionType == 2:
            for i in range(self.sizeParticles):
                vel = (random.gammavariate(10,.1), random.gammavariate(10,.1))
                acc = (random.gammavariate(10,.01), random.gammavariate(10,.01))
                point = sampleRandomPoint2dUniform(self.params["limits"])
                self.particles[i] = [point, vel, acc]

    def read_grids(self):
        self.cells, self.cellsInv, self.widthGrid, self.heightGrid, \
        self.sizeGrid = read_grids(
                self.gridFile, delimiter= "::")

        print "ParticleFilter: Grid size is " + str(self.sizeGrid)


    def prepare_grids(self, beta = 0):
        self.sizeGrid = .25
        self.cells = []
        self.cellsInv = {}

        # divide the world into grids
        self.widthGrid =  int(np.ceil(
                self.params["limits"][1][0]/self.sizeGrid)) + 1
        self.heightGrid = int(np.ceil(
                self.params["limits"][1][1]/self.sizeGrid)) + 1

        # generate cellVisuals
        for j in range(self.heightGrid):
            for i in range(self.widthGrid):
                point = (round(self.params["limits"][0][0] + i
                               *self.sizeGrid,2),
                         round(self.params["limits"][0][1] + j
                               *self.sizeGrid,2) )
                self.cellsInv[point] = i + j * self.widthGrid
                self.cells.append({})
                # self.imageScene.addPoint(real2Pix(self.params, point),
                #                          "", QtGui.QColor(0,0,0),radius=1)

                pointList = find_closest_points(point,
                                                self.pointsSelected,
                                                radius=5.0)
                pairs = find_all_pairs(point, pointList)
                if len(pairs) == 0:
                    continue
                pair = pairs[0]

                # get t value for the triplet
                t = calculate_t(point, pair[0], pair[1])

                for beacon in self.beacons:
                    s, mapping = hist_wasserstein(
                        self.dataHist[pair[0]][beacon],
                        self.dataHist[pair[1]][beacon])
                    # get the interpolation at (t, beta)
                    self.cells[-1][beacon] = \
                        hist_wasserstein_interpolation(
                        mapping, t, beta)

    def pf_importance_sampling_diffusion(self, beacon, rssi, offset = None,
                                      sigma = 1):
        # generate particles accorting to the model
        # default sigma is 1 m.
        for i in range(self.sizeParticles):
            self.particlesHat[i] = [sampleRandomPoint2dNormal(
                    self.particles[i][0],sigma)]

        # evaluate the newly generated particles
        self.pf_evaluateParticles(beacon, rssi)
        self.pf_normalize_sort_weights()

    def pf_importance_sampling_odometry(
            self, beacon, rssi, dist, orientDelta, sigma = .25):
        # generate particles according to the model
        for i in range(self.sizeParticles):
            orient = self.particles[i][1] + orientDelta
            tempParticle = (self.particles[i][0][0] + math.cos(orient) * dist,
                            self.particles[i][0][1] + math.sin(orient) * dist)

            self.particlesHat[i] = [
                sampleRandomPoint2dNormal(tempParticle,sigma),
                orient + random.normalvariate(0, sigma)]

        # evaluate the newly generated particles
        self.pf_evaluateParticles(beacon, rssi)
        self.pf_normalize_sort_weights()

    def pf_importance_sampling_acceleration(
            self, beacon, rssi, acc, deltaT, sigma = .25):
        # generate particles according to the model
        for i in range(self.sizeParticles):

            vel = (
                self.particles[i][1][0] + acc[0] * deltaT,
                self.particles[i][1][1] + acc[1] * deltaT)

            tempPoint = (
                self.particles[i][0][0] + vel[0] * deltaT,
                self.particles[i][0][1] + vel[1] * deltaT)

            point = sampleRandomPoint2dNormal(tempPoint,sigma)


            # # point
            # point = self.particles[i][0]
            #
            # # velocity
            # vel = (
            #     self.particles[i][1][0] + self.particles[i][2][0] * deltaT,
            #     self.particles[i][1][1] + self.particles[i][2][1] * deltaT)
            #
            # # current acceleration
            # point = (
            #     self.particles[i][0][0] + self.particles[i][1][0] * deltaT,
            #     self.particles[i][0][1] + self.particles[i][1][1] * deltaT)
            #
            # acc = (
            #     random.normalvariate(self.particles[i][2][0],sigma),
            #     random.normalvariate(self.particles[i][2][1],sigma)
            # )
            #
            self.particlesHat[i] = (point, vel, acc)

        # evaluate the newly generated particles
        self.pf_evaluateParticles(beacon, rssi)
        self.pf_normalize_sort_weights()

    def pf_normalize_sort_weights(self):
        if self.weights_sum == 0:
            for i in range(self.sizeParticles):
                self.particleWeights[i] = 1.0/self.sizeParticles
        else:
            for i in range(self.sizeParticles):
                self.particleWeights[i] = self.particleWeights[
                                              i]/self.weights_sum

        self.pf_sort_particles()

    def pf_mean_point(self):
        S0 = 0.0
        S1 = 0.0
        W = 0.0
        for i in range(self.sizeParticles):
            S0 += self.particles[i][0][0] * self.particleWeights[i]
            S1 += self.particles[i][0][1] * self.particleWeights[i]
            W += self.particleWeights[i]
        self.particleWeightedMean = (S0/W, S1/W)

    def pf_sort_particles(self):
        indexes = sorted(
                range(self.sizeParticles),
                key=lambda x:self.particleWeights[x],
                reverse=True)
        for i in range(self.sizeBestWeights):
            self.bestIndexes[i] = indexes[i]
            self.bestWeights[i] = self.particleWeights[indexes[i]]

    def pf_evaluateParticles(self, beacon, rssi):
        self.weights_sum = 0
        for i in range(self.sizeParticles):
            if self.pf_check_limits(self.particlesHat[i][0]):
                self.particleWeights[i] = self.pf_likelihood(
                    self.particlesHat[i][0], beacon, rssi, 0)
                self.weights_sum += self.particleWeights[i]
            else:
                self.particleWeights[i] = 0

    def pf_check_limits(self, point):
        # print self.params["limits"]
        if point[0] < self.params["limits"][0][0]:
            return False
        if point[1] < self.params["limits"][0][1]:
            return False
        if point[0] > self.params["limits"][1][0]:
            return False
        if point[1] > self.params["limits"][1][1]:
            return False
        return True

    def pf_selectParticles(self):
        # Resample N particles according to the weights
        # get an index wrt the weights
        cumul = getCumulative(self.bestWeights)
        indexes = randgen(cumul, self.sizeParticles, self.bestIndexes)
        for i in range(self.sizeParticles):
            self.particles[i] = self.particlesHat[indexes[i]]

    def pf_selectParticlesPar(self):
        cumulative = getCumulative(self.bestWeights)

        # send the cdf to the processes
        for i in range(numProcess):
            # refresh
            self.pQueues[i].put(('r'))
            # send cumulative
            self.pQueues[i].put(('c', cumulative))
            # send bestIndexes
            self.pQueues[i].put(('b', self.bestIndexes))

        # request selection
        for i in range(numProcess):
            self.pQueues[i].put(('s', self.sizeParticles/numProcess))

        # retrieve selected indexes
        c = 0
        for i in range(numProcess):
            indexes = self.doneQueue.get()
            for index in indexes:
                self.particles[c] = self.particlesHat[index]
                c += 1


    def pf_likelihood_closest(self, point, beacon, value, beta):
     # compare with the histogram at the closest fingerprint point
        if not self.dataHist:
            return

        closest = find_closest_points(point,
                                      self.dataHist.keys(),
                                      numMax=1)
        if len(closest) == 0:
            return 0
        return self.dataHist[closest[0]][beacon][int(value - self.bins[0])]

    def pf_likelihood_grids(self, point, beacon, value, beta):
        # get the closest grid point
        i = int((point[0] + self.sizeGrid/2)/ self.sizeGrid)
        j = int((point[1] + self.sizeGrid/2)/ self.sizeGrid)

        index = j * self.widthGrid + i
        return self.cells[index][beacon][value - self.bins[0]]

    def pf_likelihood_wasserstein(self, point, beacon, value, beta):
        # compare with the histogram according to the interpolation
        if not self.dataHist:
            return 0

        # find the best pair for the given point
        pointList = find_closest_points(point, self.pointsSelected,
                                        radius=1.5)
        pairs = find_all_pairs(point, pointList)
        # pairs = find_best_pair(point, pairs) # returns a list of pairs
        if len(pairs) == 0:
            return 0
        else:
            pair = pairs[0]

        # get t value for the triplet
        t = calculate_t(point, pair[0], pair[1])

        # generate the interpolation for each beacon
        # interp = {}

        if not beacon in self.dataHist[pair[0]].keys():
            return 0
        if not beacon in self.dataHist[pair[1]].keys():
            return 0

        s, mapping = hist_wasserstein(
            self.dataHist[pair[0]][beacon],
            self.dataHist[pair[1]][beacon])
        # get the interpolation at (t, beta)
        interp = hist_wasserstein_interpolation(
                mapping, t, beta)
        if not interp[value - self.bins[0]] == 0:
            return interp[value - self.bins[0]]
        else:
            return 0

        # print value, interp[value - self.bins[0]]
            # print self.particles[i]

def main():
    pQueues = []
    doneQueue = mQueue()
    for p in range(numProcess):
        q = mQueue()
        pQueues.append(q)

    bQueue = Queue.Queue()
    fQueue = Queue.Queue()
    outQueue = Queue.Queue()
    sThread = SimulationFileThread("FileThread", fQueue, outQueue)
    bThread = BluetoothThread("BluetoothThread", bQueue, outQueue)

    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    else:
        configFile = None

    trackFile = None
    if len(sys.argv) > 2:
        trackFile = sys.argv[2]

    # define processes
    processes = []
    for i in range(numProcess):
        p = Process(target=processFunction, args=(str(i), pQueues[i], doneQueue))
        processes.append(p)

    sThread.start()
    bThread.start()
    # start processes
    for p in processes:
        p.start()

    app = btViewerGui(fQueue, bQueue, outQueue, pQueues, doneQueue,
                      configFile, trackFile)

    #start sampThreads
    app.run()


    # end the threads gracefully
    for p in range(numProcess):
        pQueues[p].put("QUIT")
    bQueue.put(["QUIT", None] )
    fQueue.put(["QUIT", None] )

    for p in processes:
        p.join()

    sThread.join()
    bThread.join()

if __name__ == '__main__':
    main()

