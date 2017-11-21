from PyQt4 import QtGui
from PyQt4 import QtCore
import sys, os
from lib.btCalibrate_ui import Ui_btCalibrate
from lib.histogram_visuals import *
from lib.btQtCore import *

class btCalibrateImageScene(btImageScene):
    def __init__(self, btViewerGui):
        QtGui.QGraphicsScene.__init__(self)
        self.circleRadius = 4
        self.latestPoint = None
        self.terminals = [ None, None ]
        self.limits = [ None, None ]
        self.frame = [ None, None, None, None ]
        self.originPoint = None
        self.positiveDirLines = [ None, None, None ]
        self.tempCircle = None
        self.tempLine = None
        self.btV = btViewerGui

    def putTempCircle(self):
        # tempCircle to delete when needed
        self.tempCircle = self.addPoint(self.latestPoint,"",color =
        QtGui.QColor(255,0,0))

    def mousePressEvent(self, event):
        self.latestPoint = QtCore.QPoint(event.scenePos().x(),
                                         event.scenePos().y())
        if self.btV.ui.point1.isChecked():
            self.btV.point1 = self.latestPoint
        if self.btV.ui.point2.isChecked():
            self.btV.point2 = self.latestPoint
        if self.btV.ui.origin.isChecked():
            self.btV.params["origin"] = self.latestPoint
        if self.btV.ui.positive.isChecked():
            self.btV.params["direction"] = QtCore.QPoint(
                (self.latestPoint.x() - self.btV.params["origin"].x()) / \
                abs(self.latestPoint.x() - self.btV.params["origin"].x()),
                (self.latestPoint.y() - self.btV.params["origin"].y()) / \
                abs(self.latestPoint.y() - self.btV.params["origin"].y())
            )
        if self.btV.ui.edit.isChecked():
            self.btV.togglePressed(self.latestPoint)

        if self.btV.imageFile:
            self.placeParameters()
            self.clearParameters()
            self.putParameters()

    def clearParameters(self):
        if self.originPoint:
            self.removeItem(self.originPoint)
        if self.terminals[0]:
            self.removeItem(self.terminals[0])
        if self.terminals[1]:
            self.removeItem(self.terminals[1])
        for line in self.positiveDirLines:
            if line:
                self.removeItem(line)
        if self.tempLine:
            self.removeItem(self.tempLine)
        if self.limits[0]:
            self.removeItem(self.limits[0])
        if self.limits[1]:
            self.removeItem(self.limits[1])
        if self.frame[0]:
            for i in range(0,4):
                self.removeItem(self.frame[i])


    def placeParameters(self):
        if self.btV.params["origin"]:
            self.btV.ui.labelOrigin.setText("Origin: %s,%s" % (
                str(self.btV.params["origin"].x()), str(self.btV.params["origin"].y())))
        else:
            self.btV.ui.labelOrigin.setText("Origin:")

        if self.btV.params["direction"]:
            self.btV.ui.labelPositive.setText("Direction: %s,%s" % (
                str(self.btV.params["direction"].x()),
                str(self.btV.params["direction"].y())))
        else:
            self.btV.ui.labelPositive.setText("Direction")

        if self.btV.params["parity"]:
            self.btV.ui.labelParity.setText("Parity: %s m/px" % (
                round(float(self.btV.params["parity"]),5)))
        else:
            self.btV.ui.labelOrigin.setText("Parity:")

        if self.btV.point1:
            realCoord = pix2Real(self.btV.params,self.btV.point1)
            self.btV.ui.labelPoint1.setText("Point 1: (%s,%s), (%s,%s)" % (
                str(self.btV.point1.x()), str(self.btV.point1.y()),
                str(round(realCoord[0],2)), str(round(realCoord[1],2))))
        else:
            self.btV.ui.labelPoint1.setText("Point 1:")

        if self.btV.point2:
            realCoord = pix2Real(self.btV.params,self.btV.point2)
            self.btV.ui.labelPoint2.setText("Point 2: (%s,%s), (%s,%s)  " % (
                str(self.btV.point2.x()), str(self.btV.point2.y()),
                str(round(realCoord[0],2)), str(round(realCoord[1],2))))
        else:
            self.btV.ui.labelPoint2.setText("Point 2:")

        if self.btV.params["limits"]:
            self.btV.ui.labelLimits.setText("Limits: (%s,%s),(%s,%s)" %
                    (round(self.btV.params["limits"][0][0],2),
                     round(self.btV.params["limits"][0][1],2),
                     round(self.btV.params["limits"][1][0],2),
                     round(self.btV.params["limits"][1][1],2)))


    def putParameters(self):
        # put graphics

        if not self.btV.imageFile:
            return
        if self.btV.params["origin"]:
            self.originPoint = self.addPoint(self.btV.params["origin"],"",
                                              QtGui.QColor(0,0,0))
        if self.btV.point1:
            self.terminals[0] = self.addPoint(self.btV.point1,"",
                                              QtGui.QColor(255,255,0))
        if self.btV.point2:
            self.terminals[1] = self.addPoint(self.btV.point2,"",
                                              QtGui.QColor(255,255,0))
        if self.btV.params["origin"] and self.btV.params["direction"]:
            arrPoint = QtCore.QPoint(self.btV.params["origin"].x() +
                                self.btV.params["direction"].x() * 30,
                                     self.btV.params["origin"].y() +
                                self.btV.params["direction"].y() * 30)

            arrow1, arrow2 = self.getArrowHead(self.btV.params["origin"],
                                               arrPoint)
            self.positiveDirLines[0] = self.addLine(
                self.btV.params["origin"].x(),
                self.btV.params["origin"].y(),
                arrPoint.x(),
                arrPoint.y(),
                QtGui.QPen(QtGui.QColor(0,255,0)))

            self.positiveDirLines[1] = self.addLine(
                arrPoint.x(),
                arrPoint.y(),
                arrow1[0],
                arrow1[1],
                QtGui.QPen(QtGui.QColor(0,255,0))
            )

            self.positiveDirLines[2] = self.addLine(
                arrPoint.x(),
                arrPoint.y(),
                arrow2[0],
                arrow2[1],
                QtGui.QPen(QtGui.QColor(0,255,0))
            )

        if self.btV.point1 and self.btV.point2:
            self.tempLine = self.addLine(
                self.btV.point1.x(),
                self.btV.point1.y(),
                self.btV.point2.x(),
                self.btV.point2.y(),
                QtGui.QPen(QtGui.QColor(255,0,0)))

            # put length info
            if self.btV.params["parity"]:
                norm = math.sqrt((self.btV.point1.x() - self.btV.point2.x())**2 + \
                        (self.btV.point1.y() - self.btV.point2.y())**2) * \
                        self.btV.params["parity"]

                newText = QtGui.QGraphicsSimpleTextItem(str(round(norm,2)))
                newText.setPos(
                    (self.btV.point1.x() + self.btV.point2.x())/2 - 15,
                    (self.btV.point1.y() + self.btV.point2.y())/2
                )

                newText.setFont(QtGui.QFont('Mono',6))
                newText.setParentItem(self.tempLine)

        if self.btV.params["limits"]:
            if self.btV.params["origin"] and self.btV.params["parity"] and self.btV.params["direction"]:
                p0 = real2Pix(self.btV.params, self.btV.params["limits"][0])
                p1 = real2Pix(self.btV.params, self.btV.params["limits"][1])
                self.limits[0] = self.addPoint(
                    real2Pix(self.btV.params, self.btV.params["limits"][0]),"%s,%s" % (
                        round(self.btV.params["limits"][0][0],2),
                        round(self.btV.params["limits"][0][1],2)),
                                      QtGui.QColor(128,0,128))
                self.limits[1] = self.addPoint(
                    real2Pix(self.btV.params, self.btV.params["limits"][1]),"%s,%s" % (
                        round(self.btV.params["limits"][1][0],2),
                        round(self.btV.params["limits"][1][1],2)),
                                      QtGui.QColor(128,0,128))
                self.frame[0] = self.addLine(p0.x(),p0.y(),p0.x(),p1.y(),
                                QtGui.QPen(QtGui.QColor(255,0,255)))
                self.frame[1] = self.addLine(p0.x(),p0.y(),p1.x(),p0.y(),
                                QtGui.QPen(QtGui.QColor(255,0,255)))
                self.frame[2] = self.addLine(p0.x(),p1.y(),p1.x(),p1.y(),
                                QtGui.QPen(QtGui.QColor(255,0,255)))
                self.frame[3] = self.addLine(p1.x(),p0.y(),p1.x(),p1.y(),
                                QtGui.QPen(QtGui.QColor(255,0,255)))


class btViewerGui(QtGui.QMainWindow):
    def __init__(self, configFile):
        self.qt_app = QtGui.QApplication(sys.argv)
        QtGui.QWidget.__init__(self, None)

        # create the main ui
        self.ui = Ui_btCalibrate()
        self.ui.setupUi(self)
        self.imageScene = btCalibrateImageScene(self)
        self.pointsSelected = []
        self.fileSelected = None

        # self.colorlines = colorlines
        # self.colorlines.reverse()

        self.macColors = {}

        self.mergeList = []

        # data process
        self.ui.readDataButton.clicked.connect(self.readDataButtonPressed)
        self.dataValue = {}
        self.listFileItems = {}
        self.listFileItemsRev = {}
        self.listPointItems = {}
        self.listPointItemsRev = {}
        self.listBeaconItems = {}
        self.ui.resetDataButton.clicked.connect(self.resetDataButtonPressed)
        self.ui.mergeButton.clicked.connect(self.mergeButtonPressed)

        self.ui.pointsAvailable.clicked.connect(self.pointsAvailablePressed)
        self.ui.pointsAvailable.itemSelectionChanged.connect(
            self.pointsAvailablePressed)

        # filesAvailable
        self.ui.filesAvailable.clicked.connect(self.filesAvailablePressed)
        self.ui.filesAvailable.itemSelectionChanged.connect(self.filesAvailablePressed)

        # imageButton
        self.imageFile = None
        self.ui.loadImageButton.clicked.connect(self.loadImagePressed)
        self.ui.resetImageButton.clicked.connect(self.resetImagePressed)

        # beacons
        self.ui.loadBeaconsButton.setDisabled(True)
        self.ui.clearBeaconsButton.setDisabled(True)
        self.beaconsSet = None
        self.ui.loadBeaconsButton.clicked.connect(
            self.loadBeaconsButtonPressed)
        self.ui.clearBeaconsButton.clicked.connect(
            self.clearBeaconsButtonPressed)

        # parameters
        self.ui.saveParametersButton.clicked.connect(self.saveParametersPressed)
        self.ui.loadParametersButton.clicked.connect(self.loadParametersPressed)

        # conversion
        self.ui.loadConversionButton.clicked.connect(self.loadConversionPressed)
        self.ui.saveConversionButton.clicked.connect(self.saveConversionPressed)
        self.ui.clearConversionButton.clicked.connect(
            self.clearConversionPressed)

        self.conversion = {}
        self.conversionRev = {}

        # calibration
        self.params = {}
        self.params["parity"] = None
        self.params["origin"] = None
        self.params["direction"] = None
        self.params["limits"] = None
        self.point1 = None
        self.point2 = None
        self.ui.calibrateButton.clicked.connect(self.calibrateButtonPressed)
        self.ui.setLimitsButton.clicked.connect(self.setLimitsPressed)

        # export
        self.ui.exportBox.addItem("Histograms (daily)")
        self.ui.exportBox.addItem("Histograms (night)")
        self.ui.exportBox.addItem("Merged Data File")
        self.ui.exportBox.addItem("Histograms (daily) N")
        self.ui.exportBox.addItem("Histograms (night) N")
        self.ui.exportButton.clicked.connect(self.exportPressed)

        if configFile:
            self.configFile = configFile
            self.configFileCheck()



    def configFileCheck(self):
        try:
            with open(self.configFile, 'r') as f:
                config = json.load(f)

                if "map" in config.keys():
                    self.loadImagePressed(config["map"])
                if "par" in config.keys():
                    self.loadParametersPressed(config["par"])
                if "bea" in config.keys():
                    self.loadBeaconsFromFile(config["bea"])
                if "con" in config.keys():
                    self.loadConversionPressed(config["con"])
                print "Config file loaded: " + self.configFile
        except:
            print "Problem with the config File: " + self.configFile

    def putPointInputBox(self, point = None):
        self.Input = QtGui.QDialog(self)
        tmpPoint = (point.x(),point.y())
        self.Input.setWindowTitle("%s,%s" % tmpPoint)
        self.form = QtGui.QFormLayout(self.Input)

        if tmpPoint in self.conversionRev.keys():
            realPoint = self.conversion[self.conversionRev[tmpPoint]][1]
        else:
            realPoint = pix2Real(self.params,point)

        xValue = QtGui.QLineEdit(self.Input)
        yValue = QtGui.QLineEdit(self.Input)
        zValue = QtGui.QLineEdit(self.Input)

        labelx = QtGui.QLabel("x: ")
        labely = QtGui.QLabel("y: ")
        labelz = QtGui.QLabel("z: ")

        self.form.addRow(labelx, xValue)
        if point:
            xValue.setText(str(realPoint[0]))
            yValue.setText(str(realPoint[1]))
        if tmpPoint in self.conversionRev.keys():
            zValue.setText(str(realPoint[2]))
        else:
            zValue.setText(str(0.0))

        self.form.addRow(labely, yValue)
        self.form.addRow(labelz, zValue)

        buttonBox = QtGui.QDialogButtonBox(
            parent = self.Input,orientation = QtCore.Qt.Horizontal)
        buttonBox.setStandardButtons(
            QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)

        buttonBox.accepted.connect(self.buttonBoxAccepted)
        buttonBox.rejected.connect(self.buttonBoxRejected)

        self.form.addRow(buttonBox)
        self.Input.open()

    def run(self):
        self.show()
        sys.exit(self.qt_app.exec_())

    def resetImagePressed(self):
        self.imageScene.clear()
        self.imageFile = None
        self.ui.loadBeaconsButton.setDisabled(True)
        self.ui.noImageLabel.setVisible(True)

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

    def loadImagePressed(self, imageFile = None):
        if not imageFile:
            imageFile = QtGui.QFileDialog.getOpenFileName(self,
                                                      'Open file',
                                                      '../maps/',
                                                      'Images (*.png *.xpm '
                                                      '*.jpg)' )
        if not imageFile:
            return
        with open(imageFile, 'r') as f:
            try:
                self.imageFile = imageFile
                self.ui.loadBeaconsButton.setDisabled(False)
                # say that an image is loaded
                print "Image loaded: " + imageFile
            except:
                print "Problem with image file: " + self.imageFile
                self.imageFile = None
                self.ui.loadBeaconsButton.setDisabled(True)
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
        self.imageScene.placeParameters()
        if self.imageFile:
            self.imageScene.putParameters()
            self.ui.noImageLabel.setVisible(False)


    def loadBeaconsButtonPressed(self):
        self.loadBeaconsFromFile()

    def loadBeaconsFromFile(self, bFile = None):
        if not bFile:
            bFile = QtGui.QFileDialog.getOpenFileName(self,
                                                  'Open file',
                                                  '../conf',
                                                  'Beacon Data (*.bea)')

        if not bFile:
            return
        try:
            with open(bFile, 'r') as f:
                self.beaconsSet = {}
                beaconsTemp = json.load(f)
                for mac in beaconsTemp.keys():
                    self.beaconsSet[mac] = beaconsTemp[mac][0]
                    self.macColors[mac] = QtGui.QColor(beaconsTemp[mac][1])
                self.beaconFile = bFile
                print "Beacons loaded: " + self.beaconFile
                f.close()
        except:
            print "Incompatible File: " + bFile
            self.beaconFile = None

        finally:
            self.updateImage()

    def clearConversionPressed(self):
        self.conversionRev.clear()
        self.conversion.clear()
        self.conversionFile = None
        print "Conversions reset."

    def loadConversionPressed(self, cFile = None):
        if not cFile:
            cFile = QtGui.QFileDialog.getOpenFileName(self,
                                                  'Open file',
                                                  '../conf',
                                                  'Conversion File (*.con)')
        if not cFile:
            return
        try:
            with open(cFile, 'r') as f:
                C = json.load(f)
                self.conversion = {}
                for each in C:
                    tmp = literal_eval(each)
                    self.addConversion((tmp[0],tmp[1]),
                                       tuple(C[each][0]),
                                       tuple(C[each][1]))
                self.conversionFile = cFile
                print "Conversions loaded: " + cFile
        except:
            print "Incompatible File: " + cFile
            self.conversionFile = None
        finally:
            self.updateImage()

    def togglePressed(self, point):
        # gercek koordinatlara cevirip oyle en yakini buluyoruz
        realPoint = pix2Real(self.params, point)
        realPoints = {}
        for pts in self.dataValue[self.fileSelected].keys():
            realPoints[pix2Real(self.params, QtCore.QPoint(pts[0], pts[1]))] \
                = pts

        closest = find_closest_points(
                realPoint,realPoints.keys(),2.0, numMax=1)

        if realPoints[closest[0]] in self.pointsSelected:
            self.listPointItems[realPoints[closest[0]]].setSelected(False)
            self.pointsAvailablePressed()
        else:
            self.listPointItems[realPoints[closest[0]]].setSelected(True)
            self.pointsAvailablePressed()

    def saveConversionPressed(self):
        conFile = QtGui.QFileDialog.getSaveFileName(self,
                                                    'Save file',
                                                    '../conf',
                                                    'Conversions '
                                                    '(*.con)')

        with open(conFile, 'w') as f:
            print "Writing to file: "  + conFile
            tempConv = {}
            for each in self.conversion.keys():
                tempConv[str(each)] = self.conversion[each]
            json.dump(tempConv,f)
            print "Parameters saved to " + os.path.basename(str(
                conFile)) + "."

    def putBeacons(self):
        if self.imageFile and self.beaconsSet:
            self.ui.clearBeaconsButton.setDisabled(False)
            # colorize item list
            for mac in self.beaconsSet.keys():
                if mac in self.macColors.keys():
                    color = self.macColors[mac]
                else:
                    color = QtGui.QColor(255,255,255)

                point = tuple(self.beaconsSet[mac])
                if point in self.conversion.keys():
                    newPoint = QtCore.QPoint(
                        self.conversion[point][0][0],
                        self.conversion[point][0][1])
                else:
                    newPoint = QtCore.QPoint(
                        point[0],
                        point[1])
                self.imageScene.addPoint(newPoint, mac[-5:], color,
                                         editable=True)

    def clearBeaconsButtonPressed(self):
        self.beaconsSet.clear()
        self.ui.clearBeaconsButton.setDisabled(True)
        self.updateImage()

    def putPoints(self):
        if self.fileSelected:
            for each in self.dataValue[self.fileSelected].keys():
                if each in self.listPointItems:
                    if self.listPointItems[each].isSelected():
                        self.imageScene.addPoint(QtCore.QPoint(
                                                each[0],
                                                each[1]),
                                                str(each[0])+","+str(each[1]),
                                                QtGui.QColor(0,0,0),
                                                pencolor=QtGui.QColor(0,0,0),
                                                editable = True)
                    else:
                        self.imageScene.addPoint(QtCore.QPoint(
                                                each[0],
                                                each[1]),
                                                str(each[0])+","+str(each[1]),
                                                QtGui.QColor(255,255,255),
                                                pencolor=QtGui.QColor(0,0,0),
                                                editable = True)

    def clearPointsButtonPressed(self):
        self.updateImage()
        self.ui.clearPointsButton.setDisabled(True)

    def setLimitsPressed(self):
        if self.params["parity"] \
                and self.params["origin"] \
                and self.params["direction"] \
                and self.point1 \
                and self.point2:

            self.params["limits"] = (pix2Real(self.params, self.point1),
                                     pix2Real(self.params, self.point2))
            self.imageScene.placeParameters()
            self.updateImage()

    def calibrateButtonPressed(self):
        if self.point1 and self.point2:
            self.params["parity"] =  float(self.ui.meterBox.text()) /  \
                  math.sqrt((self.point1.x() - self.point2.x())**2 + \
                (self.point1.y() - self.point2.y())**2)
            self.ui.labelParity.setText("Parity: %s m/px"
                                        % round(self.params["parity"],5))

    def saveParametersPressed(self):
        parFile = QtGui.QFileDialog.getSaveFileName(self,
                                                    'Save file',
                                                    '../conf',
                                                    'Parameters '
                                                    '(*.par)')

        tempParams = dict(self.params)
        tempParams["origin"] = ( tempParams["origin"].x(),
                                 tempParams["origin"].y() )
        tempParams["direction"] = (tempParams["direction"].x(),
                                  tempParams["direction"].y())
        tempParams["limits"] = (tempParams["limits"][0][0],
                                tempParams["limits"][0][1],
                                tempParams["limits"][1][0],
                                tempParams["limits"][1][1])
        if not parFile:
            return
        with open(parFile, 'w') as f:
            print "Writing to file: " + parFile
            json.dump(tempParams, f)
            print "Parameters saved to " + os.path.basename(str(
                parFile)) + "."


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


    def readDataButtonPressed(self):
        self.dataFileNames = QtGui.QFileDialog.getOpenFileNames(self,
                                                              'Open file',
                                                              '../data',
                                                              'Log File ('
                                                              '*.csv)')

        if not self.dataFileNames:
            return

        # progress dialog patch

        bar = QtGui.QProgressDialog(self)
        bar.setWindowTitle("Working...")
        bar.setRange(0,0)
        bar.setMinimumDuration(100)
        bar.setMaximum(len(self.dataFileNames))
        bar.setCancelButton(None)
        bar.open()
        p = 0
        bar.setValue(p)

        for dataFile in self.dataFileNames:
            if dataFile in self.mergeList:
                continue
            with open(dataFile, 'r') as f:
                self.dataValue[dataFile] = {}

                # readfile
                for line in f:
                    each = line.split(',')
                    point = (int(each[2]),int(each[3]))
                    mac = each[4].strip()

                    if point not in self.dataValue[dataFile].keys():
                        self.dataValue[dataFile][point] = []

                        # progress bar patch
                        p +=1
                        bar.setValue(p)

                    if mac not in self.dataValue[dataFile][point]:
                        self.dataValue[dataFile][point].append(mac)

                    # color info should come from the bea file
                    # if mac not in self.macColors.keys():
                    #     r,g,b = self.colorlines.pop()
                    #     self.macColors[mac] = QtGui.QColor(r,g,b)

                if f:
                    print "Data file loaded "+ dataFile
                else:
                    print "Incompatible data file: " + dataFile

            # progressing bar

        bar.cancel()
        self.resetLists()

    def resetLists(self):
        if len(self.dataValue) > 0:
            if self.imageFile:
                self.updateImage()

            for dataFile in sorted(self.dataValue.keys()):
                if dataFile not in self.listFileItems:
                    shortFile = str(os.path.basename(str(dataFile)))
                    itemFile = QtGui.QListWidgetItem("%s" % shortFile)
                    self.listFileItems[dataFile] = itemFile
                    self.listFileItemsRev[shortFile] = dataFile
                    self.ui.filesAvailable.addItem(itemFile)

    def filesAvailablePressed(self):
        if len(self.ui.filesAvailable.selectedItems()) > 0:
            self.fileSelected = self.listFileItemsRev[
                str(self.ui.filesAvailable.selectedItems()[0].text())]
            points = self.dataValue[self.fileSelected]
            self.ui.pointsAvailable.clear()
            self.listPointItems.clear()
            for point in points.keys():
                # fast conversion update patch
                if point in self.conversion.keys():
                    self.updateDataPoints(point, self.conversion[point][0])
                    itemPoint = QtGui.QListWidgetItem(
                        "%s,%s" % (self.conversion[point][0][0],
                                   self.conversion[point][0][1]))
                else:
                    itemPoint = QtGui.QListWidgetItem("%s,%s" %
                                                      (point[0], point[1]))
                self.ui.pointsAvailable.addItem(itemPoint)
                if (point[0], point[1]) in self.conversionRev.keys():
                    itemPoint.setTextColor(QtGui.QColor(0,192,0))
                self.listPointItems[point] = itemPoint
                self.listPointItemsRev[itemPoint] = point
        else:
            self.ui.pointsAvailable.clear()
            self.listPointItems.clear()
            self.listPointItemsRev.clear()


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
                for b in self.dataValue[self.fileSelected][point]:
                    if b not in beacons.keys():
                        beacons[b] = []
                    beacons[b].append(point)

            self.ui.beaconsAvailable.clear()
            self.listBeaconItems.clear()
            for mac in beacons.keys():
                if mac in self.macColors.keys():
                    color = self.macColors[mac]
                else:
                    color = QtGui.QColor(0,0,0)
                if len(beacons[mac]) > 1:

                    itemBeacon = QtGui.QListWidgetItem("%s (%s)" % (
                            mac.strip(), len(beacons[mac])))

                    itemBeacon.setTextColor(color)
                    self.ui.beaconsAvailable.addItem(itemBeacon)
                    self.listBeaconItems[mac] = itemBeacon
                else:
                    itemBeacon = QtGui.QListWidgetItem("%s" % mac.strip())
                    itemBeacon.setTextColor(color)
                    self.ui.beaconsAvailable.addItem(itemBeacon)
                    self.listBeaconItems[mac] = itemBeacon
                if mac in beaconsBefore:
                    if itemBeacon:
                        itemBeacon.setSelected(True)

        else:
            self.ui.beaconsAvailable.clear()
            self.listBeaconItems.clear()

        if self.imageFile and len(self.dataValue) > 0:
            self.updateImage()

    def resetDataButtonPressed(self):
        self.dataValue.clear()
        self.mergeList = []
        self.ui.filesAvailable.clear()
        self.ui.pointsAvailable.clear()
        self.ui.beaconsAvailable.clear()
        self.listFileItems.clear()
        self.listFileItemsRev.clear()
        self.listPointItems.clear()
        self.listPointItemsRev.clear()
        self.fileSelected = None

    def mergeButtonPressed(self):
        tempValue = {}
        newFile = "Merged"
        tmpMergeList = list(self.mergeList)

        tempValue[newFile] = {}

        # first copy the previously merged values
        if newFile in self.dataValue.keys():
            for point in self.dataValue[newFile].keys():
                if not point in tempValue[newFile].keys():
                    tempValue[newFile][point] = []

                for mac in self.dataValue[newFile][point]:
                    if not mac in tempValue[newFile][point]:
                        tempValue[newFile][point].append(mac)

        # then add the new ones
        for file in self.dataValue.keys():
            if not file in tmpMergeList and not str(file) == newFile:
                for point in self.dataValue[file].keys():
                    if not point in tempValue[newFile].keys():
                        tempValue[newFile][point] = []

                    for mac in self.dataValue[file][point]:
                        if not mac in tempValue[newFile][point]:
                            tempValue[newFile][point].append(mac)

                tmpMergeList.append(file)


        self.resetDataButtonPressed()
        self.dataValue = tempValue
        self.mergeList = tmpMergeList
        self.resetLists()

        print("Files Merged: ")
        for file in self.mergeList:
            print "\t" + file


    def buttonBoxAccepted(self):
        # retrieve and remove the points pressed
        oldPoint = (self.circleRemove.truePoint.x(),
                       self.circleRemove.truePoint.y())

        # create a new point with the new values
        newPoint = real2Pix(self.params,(float(self.Input.children()[1].text()),
                            float(self.Input.children()[2].text())))
        newPoint = (newPoint.x(), newPoint.y())

        # update the conversion
        self.addConversion(
            oldPoint,
            newPoint,
            (float(self.Input.children()[1].text()),
             float(self.Input.children()[2].text()),
             float(self.Input.children()[3].text())
             )
            )

        self.filesAvailablePressed()
        self.pointsAvailablePressed()
        self.Input.close()

    def addConversion(self, pointFrom, pointTo, pointReal):
        if pointFrom in self.conversionRev.keys():
            print "Conversion edited:", pointFrom, "->", pointTo
            tmpFrom = self.conversionRev[pointFrom]

            # pop out oldies
            self.conversion.pop(tmpFrom)
            self.conversionRev.pop(pointFrom)

            # insert goldies
            self.conversion[tmpFrom] = (pointTo, pointReal)
            self.conversionRev[pointTo] = tmpFrom
        else:
            self.conversion[pointFrom] = (pointTo, pointReal)
            self.conversionRev[pointTo] = pointFrom
            print "Conversion added:", pointFrom, "->", pointTo
            # print self.conversion[pointFrom]

        # update the corresponding data point
        # self.updateDataPoints(pointFrom, pointTo)
        self.updateImage()
        self.filesAvailablePressed()


    def updateDataPoints(self, pointRemove, pointInstead):
        if not self.fileSelected in self.dataValue.keys():
            return
        if not pointRemove in self.dataValue[self.fileSelected].keys():
            return
        tmp = self.dataValue[self.fileSelected].pop(pointRemove)
        self.dataValue[self.fileSelected][pointInstead] = tmp

    def exportPressed(self):
        exportIndex = self.ui.exportBox.currentIndex()

        if exportIndex == 0:
            fileFilter = 'Fingerprint file (*.hst)'
        if exportIndex == 1:
            fileFilter = 'Fingerprint file (*.hst)'
        if exportIndex == 2:
            fileFilter = 'Log file (*.csv)'
        if exportIndex == 3:
            fileFilter = 'Fingerprint file (*.hst)'
        if exportIndex == 4:
            fileFilter = 'Fingerprint file (*.hst)'

        outputFile = QtGui.QFileDialog.getSaveFileName(self,
                                                    'Save file',
                                                    '../data',
                                                    fileFilter)

        if not outputFile:
            return

        if exportIndex == 0:
            self.exportHistogram(outputFile)
        if exportIndex == 1:
            self.exportHistogram(outputFile, hour = 3)
        if exportIndex == 2:
            self.exportData(outputFile)
        if exportIndex == 3:
            self.exportHistogram(outputFile, normalize=True)
        if exportIndex == 4:
            self.exportHistogram(outputFile, hour = 3, normalize=True)

    def exportData(self, outputFile):
        # progress dialog patch
        bar = QtGui.QProgressDialog(self)
        bar.setWindowTitle("Please Wait")
        bar.setMinimum(0)
        bar.setMaximum(len(self.listFileItems) + len(self.mergeList))
        bar.setCancelButton(None)
        bar.open()
        progress = 0
        bar.setValue(progress)

        with open(outputFile, 'w') as fOut:
            print "Writing to file: "  + outputFile
            for file in self.listFileItems:
                progress += 1
                bar.setValue(progress)

                if file == 'Merged':
                    continue
                print "Reading from: " + file
                with open(file, 'r') as fIn:
                    for line in fIn:
                        each = line.split(',')
                        timeStamp = each[0]
                        map = each[1]
                        point = (int(each[2]),int(each[3]))
                        if point in self.conversion.keys():
                            newPoint = self.conversion[point][0]
                        else:
                            newPoint = point
                        mac = each[4]
                        rssi = each[5]
                        fOut.write(timeStamp + "," + \
                              map + ", " + \
                              str(newPoint[0]) + ", " + \
                              str(newPoint[1]) + "," + \
                              mac + "," + \
                              rssi)

            for file in self.mergeList:

                progress += 1
                bar.setValue(progress)

                print "Reading from: " + file
                with open(file, 'r') as fIn:
                    for line in fIn:
                        each = line.split(',')
                        timeStamp = each[0]
                        map = each[1]
                        point = (int(each[2]),int(each[3]))
                        if point in self.conversion.keys():
                            newPoint = self.conversion[point][0]
                        else:
                            newPoint = point
                        mac = each[4]
                        rssi = each[5]
                        fOut.write(timeStamp + "," + \
                              map + ", " + \
                              str(newPoint[0]) + ", " + \
                              str(newPoint[1]) + "," + \
                              mac + "," + \
                              rssi)
            bar.close()

    def exportHistogram(self, outputFile, hour = None, normalize = False):

        beacons = {}
        points = {}
        if not self.beaconsSet or len(self.beaconsSet) == 0:
            print "Beacons not loaded"
            return

        if len(self.conversion) == 0:
            print "Conversions not loaded"
            return

        for beacon in self.beaconsSet.keys():
            beacons[beacon] = \
                [ self.conversion[tuple(self.beaconsSet[beacon])][1],
                  self.macColors[beacon].rgb() ]

        # progress dialog patch
        bar = QtGui.QProgressDialog(self)
        bar.setWindowTitle("Please Wait")
        bar.setMinimum(0)
        bar.setMaximum(len(self.listFileItems) + len(self.mergeList))
        bar.setCancelButton(None)
        bar.open()
        progress = 0
        bar.setValue(progress)

        # dosyalari okuyup histogram olustur
        for file in self.dataValue.keys():
            progress += 1
            bar.setValue(progress)
            if file == "Merged":
                continue
            dataValue, dataTime, dataHist, bins, dataColors = parse_data_file(
                str(file), coloring=False, hour=hour, normalize= normalize)
            for pts in dataHist.keys():
                if not self.conversion[pts][0] in self.pointsSelected:
                    continue

                print ("Writing: " + str(pts))
                if pts not in self.conversion.keys():
                    print("Conversion not found: " + str(pts))
                    bar.close()
                    return

                point3d = str(self.conversion[pts][1])
                if point3d in points.keys():
                    print("Warning: The point exists!")
                else:
                    points[point3d] = {}

                for mac in dataHist[pts].keys():
                    points[point3d][mac] = list(dataHist[pts][mac])

        for file in self.mergeList:
            progress += 1
            bar.setValue(progress)
            dataValue, dataTime, dataHist, bins, dataColors = parse_data_file(
                str(file), coloring=False, hour= hour, normalize= normalize)
            for pts in dataHist.keys():
                if not self.conversion[pts][0] in self.pointsSelected:
                    continue

                if pts not in self.conversion.keys():
                    print("Conversion not found: " + str(pts))
                    bar.close()
                    return

                point3d = str(self.conversion[pts][1])
                if point3d in points.keys():
                    print("Warning: The point exists!")
                else:
                    points[point3d] = {}

                for mac in dataHist[pts].keys():
                    points[point3d][mac] = list(dataHist[pts][mac])

        bar.close()

        # write file
        with open(outputFile, 'w') as f:
            print "Writing to file: "  + outputFile
            f.write("Beacons:")
            json.dump(beacons,f)
            f.write("\n")
            f.write("Fingerprints:")
            json.dump(points,f)
            f.write("\n")
            f.write("Bins:")
            json.dump(list(bins),f)
            f.write("\n")

            f.close()
            print "Fingerprint histograms saved to " + os.path.basename(str(
                outputFile)) + "."

    def buttonBoxRejected(self):
        # do nothing
        self.Input.close()

def main():

    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    else:
        configFile = None

    app = btViewerGui(configFile)
    app.run()

if __name__ == '__main__':
    main()
