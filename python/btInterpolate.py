from PyQt4 import QtGui
from PyQt4 import QtCore
import sys, os, time
from lib.btInterpolate_ui import Ui_btInterpolate
from lib.histograms import *
from lib.histogram_visuals import *
from lib.btQtCore import *

class InterpolateImageScene(btImageScene):
    def __init__(self, btViewerGui):
        QtGui.QGraphicsScene.__init__(self)
        self.circleRadius = 4
        self.latestPoint = [ None, None ]
        self.originPoint = None
        self.positiveDirLines = [ None, None, None ]
        self.tempCircle = None
        self.btV = btViewerGui
        self.pairs = []
        self.limits = [ None, None ]
        self.frame = [ None, None, None, None ]


    def setImageSize(self, size):
        self.sizeX = size.width()
        self.sizeY = size.height()

    def putTempCircle(self):
        # tempCircle to delete when needed
        if self.latestPoint[0]:
            self.tempCircle = self.addPoint(self.latestPoint[0],"",color =
            QtGui.QColor(255,0,0))

    def mousePressEvent(self, event):
        self.latestPoint[0] = QtCore.QPoint(event.scenePos().x(),
                                         event.scenePos().y())
        self.latestPoint[1] = pix2Real(self.btV.params, self.latestPoint[0])

        if self.btV.params["parity"]:
            # self.pairs, t = self.btV.find_point_pairs(pix2Real(
            #     self.latestPoint))

            # self.latestPoint, self.pairs = self.btV.find_closest_points(
            #     pix2Real(self.latestPoint))

            if self.btV.betavsPairs:
                # get the closest point
                tempPoint = find_closest_points(
                    pix2Real(self.btV.params, self.latestPoint[0]),
                    self.btV.dataHist.keys(),
                    numMax=1)

                self.latestPoint[1] = tempPoint[0]

                # get its pix coordinates
                self.latestPoint[0] = QtCore.QPoint(
                    real2Pix(self.btV.params, self.latestPoint[1]))

                # get the pairs from the betavsPairs
                self.pairs = []
                for beacon in self.btV.betavsPairs.keys():
                    if self.latestPoint[1] \
                            in self.btV.betavsPairs[beacon].keys():
                        self.pairs.append(
                            (tuple(self.btV.betavsPairs[beacon][self.latestPoint[
                                1]][0][0]),
                            tuple(self.btV.betavsPairs[beacon][self.latestPoint[
                                1]][0][1]),
                             beacon,
                             self.btV.betavsPairs[beacon][self.latestPoint[
                                 1]][1],
                             self.btV.betavsPairs[beacon][self.latestPoint[
                                 1]][2])
                        )
                self.btV.updateImage()

            else:
                points, self.pairs = self.btV.find_best_pair(
                        self.latestPoint[1])
                
                self.btV.updateImage()
            if self.latestPoint[0]:
                if len(self.pairs) > 0:
                    t = calculate_t(self.latestPoint[1],
                                    self.pairs[0][0],
                                    self.pairs[0][1])
                    self.btV.plotHists(self.latestPoint[1], self.pairs[0], t)
                else:
                    self.btV.plotHists(self.latestPoint[1], [])

class btViewerGui(QtGui.QMainWindow):
    def __init__(self, configFile = None):
        self.qt_app = QtGui.QApplication(sys.argv)
        QtGui.QWidget.__init__(self, None)

        # create the main ui
        self.ui = Ui_btInterpolate()
        self.ui.setupUi(self)
        self.imageScene = InterpolateImageScene(self)
        self.pointsSelected = []

        self.colorlines = colorlines
        self.colorlines.reverse()

        self.macColors = {}
        self.dataHist = {}
        self.beacons = None
        self.bins = None
        self.hl0 = self.ui.histView0.addPlot()
        self.hl1 = self.ui.histView1.addPlot()
        self.hl2 = self.ui.histView2.addPlot()

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

        # sliders
        self.ui.sliderBeta.valueChanged.connect(self.updateSliders)
        self.ui.sliderR.valueChanged.connect(self.updateSliders)
        self.ui.sliderT.valueChanged.connect(self.updateSliders)
        self.ui.sliderTheta.valueChanged.connect(self.updateSliders)
        self.ui.sliderTheta.setDisabled(True)
        self.ui.thetaBox.toggled.connect(self.updateTheta)
        self.ui.sliderR.setValue(50)

        # config file
        if configFile:
            self.configFile = configFile
            self.configFileCheck()

        # previously computed pairs and beta
        self.ui.loadBetavsPairsButton.clicked.connect(self.betavsPairsPressed)
        self.betavsPairs = None

        # for fps
        self.lastDataTime = []

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


    def run(self):
        self.show()
        self.qt_app.exec_()

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

    def updateTheta(self):
        if self.ui.thetaBox.isChecked():
            self.ui.sliderTheta.setDisabled(False)
            self.updateSliders()
        else:
            self.ui.sliderTheta.setDisabled(True)
            self.ori = None

    def updateSliders(self):
        self.ui.t.setText("t: %s" % (self.ui.sliderT.value()/100.0))
        self.ui.beta.setText("%s: %s" % (QtCore.QChar(946),
                                      self.ui.sliderBeta.value()/ 100.0))
        self.ui.theta.setText("%s: %s" % (QtCore.QChar(952),
                          (self.ui.sliderTheta.value()-50.0) / 50.0))
        if not self.params['limits'] == None:
            self.ui.r.setText("r: %s" % (
                self.ui.sliderR.value()/ 100.0 *
                (round(math.sqrt(
                    self.params["limits"][1][0]**2 +
                    self.params["limits"][1][1]**2
                ),2)
            )))

        if self.ui.sliderTheta.isEnabled():
            self.ori = (self.ui.sliderTheta.value()-50.0)/ 50.0

        if len(self.imageScene.pairs) > 0  and \
                self.imageScene.latestPoint[0]:
            self.plotHists(self.imageScene.latestPoint[1],
                self.imageScene.pairs[0])

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


    def updateImage(self):
        self.frame = QtGui.QImage(self.imageFile)
        self.frame = self.setOpacity(0.2)
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
            self.imageScene.putTempCircle()



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
                    if pts in ptsList[0:2]:
                        self.imageScene.addPoint(
                                real2Pix(self.params,pts),
                                str(pts[0])+","+str(pts[1]),
                                QtGui.QColor(255,255,0),
                                pencolor=QtGui.QColor(0,0,0),
                                radius= 4)
                    else:
                        self.imageScene.addPoint(
                                real2Pix(self.params,pts),
                                str(pts[0])+","+str(pts[1]),
                                QtGui.QColor(0,255,0),
                                pencolor=QtGui.QColor(0,0,0),
                                radius= 4)


                else:
                    if self.listPointItems[pts].isSelected():
                        self.imageScene.addPoint(
                                real2Pix(self.params,pts),
                                str(pts[0])+","+str(pts[1]),
                                QtGui.QColor(0,0,0),
                                pencolor=QtGui.QColor(0,0,0),
                                radius= 4)
                    else:
                        self.imageScene.addPoint(
                                real2Pix(self.params, pts),
                                str(pts[0])+","+str(pts[1]),
                                QtGui.QColor(255,255,255),
                                pencolor=QtGui.QColor(0,0,0),
                                radius= 4)

        if self.imageScene.latestPoint[1]:
            self.ui.mousePoint.setText(str(
                    (round(self.imageScene.latestPoint[1][0],3),
                     round(self.imageScene.latestPoint[1][1],3))
            ))


        self.putLines()

    def putLines(self):
        pairSeen = []
        # bir pair daha once gorulduyse 2 piksel offset ekle
        if len(self.imageScene.pairs) == 0:
            return
        if len(self.imageScene.pairs[0]) == 0:
            return
        for pair in self.imageScene.pairs:
            if len(pair) > 2:
                pen = QtGui.QPen(QtGui.QColor(self.macColors[pair[2]]))
                newText = QtGui.QGraphicsSimpleTextItem(
                    "%s,%s" % (round(pair[3],1), round(pair[4],3)))
                pen.setWidth(2)
            else:
                pen = QtGui.QPen(QtGui.QColor(0,0,0))
            p1 = real2Pix(self.params, pair[0])
            p2 = real2Pix(self.params, pair[1])
            tempLine = self.imageScene.addLine(
                p1.x(),
                p1.y(),
                p2.x(),
                p2.y(),
                pen)

            if len(pair) > 2:
                newText.setPos(
                    p1.x() + (p2.x() - p1.x())/8 - 10,
                    p1.y() + (p2.y() - p1.y())/8
                )
                newText.setPen(pen)
                newText.setFont(QtGui.QFont('Mono',8))
                newText.setParentItem(tempLine)





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

    def find_closest_points(self, point):
        # find the closest point
        points = find_closest_points(point, self.dataHist.keys(), numMax=1)
        latest = points[0]
        # find the closest points to the selected single point
        points = find_closest_points(latest, self.dataHist.keys())
        pairs = find_all_pairs(latest, points, ori=self.ori)
        return latest, pairs

    def find_best_pair(self, point):
        # points = find_closest_points(point, self.dataHist.keys(), numMax=1)
        # latest = points[0]
        radius = self.ui.sliderR.value() / 100.0 * round(math.sqrt(
                self.params["limits"][1][0]**2 +
                self.params["limits"][1][1]**2
            ),2)
        points = find_closest_points(point, self.dataHist.keys(), radius)
        pairs = find_all_pairs(point, points, ori=self.ori)
        # pair = find_best_pair(latest,pairs)
        return point, pairs

    def plotHists(self, point, pair, t = None):
        # rssiRange = [min(self.bins), max(self.bins)]
        self.hl0.clear()
        self.hl1.clear()
        self.hl2.clear()
        mapping = {}
        W = {}
        midhist = {}

        # read parameters
        if not t:
            t = self.ui.sliderT.value()/100.0
        else:
            self.ui.sliderT.setValue(int(t*100))
        beta = self.ui.sliderBeta.value()/100.0

        for beaconItem in self.ui.beaconsAvailable.selectedItems():
            mac = str(beaconItem.text())[0:17]

            tempColor = QtGui.QColor(self.macColors[mac])
            tempColor.setAlpha(50)

            if point in self.dataHist.keys():
                self.hl0.plot(self.bins[:-1],
                    hist_normalize(self.dataHist[point][mac]),
                    pen = {'color': tempColor, 'width': 2})
                self.hl0.setYRange(0,.5)

            if not pair:
                continue

            self.hl1.plot(self.bins[:-1],
                hist_normalize(self.dataHist[pair[0]][mac]),
                pen = {'color': QtGui.QColor(self.macColors[mac]), 'width' : 2})
            self.hl1.setYRange(0,.5)

            self.hl2.plot(self.bins[:-1],
                hist_normalize(self.dataHist[pair[1]][mac]),
                pen = {'color': QtGui.QColor(self.macColors[mac]), 'width' : 2})
            self.hl2.setYRange(0,.5)

            W[mac], mapping[mac] =\
                hist_wasserstein(
                    self.dataHist[pair[0]][mac],
                    self.dataHist[pair[1]][mac]
                )
            midhist[mac] = hist_wasserstein_interpolation(
                mapping[mac],t,beta
            )

            self.hl0.plot(self.bins[:-1],
                hist_normalize(midhist[mac]),
                pen = {'color': QtGui.QColor(self.macColors[mac]), 'width' : 2})
            self.hl0.setYRange(0,.5)

    def betavsPairsPressed(self, betaFile = None):
        if not betaFile:
            betaFile = QtGui.QFileDialog.getOpenFileName(self,
                                                  'Open file',
                                                  './data',
                                                  'BetavsPairs (*.bet)')

            # parse beta file
            self.betavsPairs = betaParser(betaFile)

def main():

    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    else:
        configFile = None

    app = btViewerGui(configFile)
    app.run()

if __name__ == '__main__':
    main()

