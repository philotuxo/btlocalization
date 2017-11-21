from PyQt4 import QtGui
from PyQt4 import QtCore
import sys, os, time
from lib.btViewer_ui import Ui_BeaconView
import itertools
from lib.histograms import *

class extImageScene(QtGui.QGraphicsScene):
    def __init__(self, btViewerGui):
        QtGui.QGraphicsScene.__init__(self)
        self.circleRadius = 4
        self.latestPoint = None
        self.tempEllipse = None
        self.btV = btViewerGui

    def setImageSize(self, size):
        self.sizeX = size.width()
        self.sizeY = size.height()

    def addPoint(self, point, text, color):
        xoffset = 14
        yoffset = 10
        br = QtGui.QBrush()
        br.setStyle(1) # RadialGradient pattern
        br.setColor(color)
        brText = QtGui.QBrush()
        brText.setStyle(1) # RadialGradient pattern
        brText.setColor(QtGui.QColor(96,96,96))
        newEllipse = QtGui.QGraphicsEllipseItem(
                        point.x() - self.circleRadius,
                        point.y() - self.circleRadius,
                        2* self.circleRadius,
                        2* self.circleRadius)
        newEllipse.setBrush(br)
        if point.x() > self.circleRadius \
                and point.y() > self.circleRadius \
                and point.x() < self.sizeX - self.circleRadius \
                and point.y() < self.sizeY - self.circleRadius:


            if point.x() < xoffset:
                text_x = xoffset
            elif point.x() > self.sizeX - xoffset:
                text_x = self.sizeX - 2 * xoffset
            else:
                text_x = point.x() - xoffset

            if point.y() < yoffset:
                text_y = 2 * yoffset
            elif point.y() > self.sizeY - yoffset:
                text_y = self.sizeY - 2* yoffset
            else:
                text_y = point.y() - 2 * yoffset

            if len(text) > 5:
                newText = QtGui.QGraphicsSimpleTextItem(text)
                newText.setPos(
                    text_x,
                    text_y
                )
            else:
                newText = QtGui.QGraphicsSimpleTextItem(text)
                newText.setPos(
                    text_x + xoffset - 5,
                    text_y
                )

            newText.setFont(QtGui.QFont('Mono',6))
            newText.setParentItem(newEllipse)

            newText.setBrush(brText)
            self.addItem(newEllipse)
        return newEllipse


    def putTempEllipse(self):
        self.tempEllipse = self.addPoint(self.latestPoint,"",color =
        QtGui.QColor(255,0,0))


    def mousePressEvent(self, event):
        if self.btV.activeTab == 2:
            self.latestPoint = QtCore.QPoint(event.scenePos().x(),
                                             event.scenePos().y())
            if self.tempEllipse:
                self.removeItem(self.tempEllipse)
            self.putTempEllipse()
            self.btV.interpolationChanged()
        elif self.btV.activeTab == 3:
            pass
        else:
            self.latestPoint = None
            if self.tempEllipse:
                self.removeItem(self.tempEllipse)



class btViewerGui(QtGui.QMainWindow):
    def __init__(self):
        self.qt_app = QtGui.QApplication(sys.argv)
        QtGui.QWidget.__init__(self, None)

        # plot parameters
        self.RssiMax = -40
        self.RssiMin = -120

        # create the main ui
        self.ui = Ui_BeaconView()
        self.ui.setupUi(self)
        self.imageScene = extImageScene(self)
        self.pointsSelected = []
        self.fileSelected = None

        self.colorlines = colorlines
        self.colorlines.reverse()

        self.macColors = {}

        # data process
        self.ui.readDataButton.clicked.connect(self.readDataButtonPressed)
        self.dataTime = {}
        self.dataValue = {}
        self.listFileItems = {}
        self.listFileItemsRev = {}
        self.listPointItems = {}
        self.listPointItemsRev = {}
        self.listBeaconItems = {}
        self.hists = {}
        self.bins = range(self.RssiMin,self.RssiMax)
        self.ui.resetDataButton.clicked.connect(self.resetDataButtonPressed)
        self.ui.mergeButton.clicked.connect(self.mergeButtonPressed)

        # plots
        self.pl = self.ui.plotTimeView.addPlot()
        self.pl.setYRange(self.RssiMin, self.RssiMax)
        self.pl.showGrid(alpha=.5, x=True, y = True)

        # time series plot
        self.ui.timeSeriesButton.clicked.connect(self.timeSeriesButtonPressed)

        # histogram plot
        self.hl = []
        self.hl.append(self.ui.plotHistView.addPlot())
        self.hl.append(self.ui.plotHistView_2.addPlot())
        self.hl.append(self.ui.plotHistView_3.addPlot())
        self.hl.append(self.ui.plotHistView_4.addPlot())
        # self.hl.append(self.ui.plotHistView_5.addPlot())
        # self.hl.append(self.ui.plotHistView_6.addPlot())
        # self.hl.append(self.ui.plotHistView_7.addPlot())

        self.rssiRange = np.arange(self.RssiMin, self.RssiMax, 1)

        self.ui.histogramButton.clicked.connect(
            lambda: self.histogramButtonPressed(0))
        self.ui.histResetButton.clicked.connect(
            lambda: self.histResetButtonPressed(0))
        self.ui.histogramButton_2.clicked.connect(
            lambda: self.histogramButtonPressed(1))
        self.ui.histResetButton_2.clicked.connect(
            lambda: self.histResetButtonPressed(1))
        self.ui.histogramButton_3.clicked.connect(
            lambda: self.histogramButtonPressed(2))
        self.ui.histResetButton_3.clicked.connect(
            lambda: self.histResetButtonPressed(2))
        self.ui.histogramButton_4.clicked.connect(
            lambda: self.histogramButtonPressed(3))
        self.ui.histResetButton_4.clicked.connect(
            lambda: self.histResetButtonPressed(3))
        # self.ui.histogramButton_5.clicked.connect(
        #     lambda: self.histogramButtonPressed(4))
        # self.ui.histResetButton_5.clicked.connect(
        #     lambda: self.histResetButtonPressed(4))
        # self.ui.histogramButton_6.clicked.connect(
        #     lambda: self.histogramButtonPressed(5))
        # self.ui.histResetButton_6.clicked.connect(
        #     lambda: self.histResetButtonPressed(5))
        # self.ui.histogramButton_7.clicked.connect(
        #     lambda: self.histogramButtonPressed(6))
        # self.ui.histResetButton_7.clicked.connect(
        #     lambda: self.histResetButtonPressed(6))

        # listboxes
        self.ui.selectAllButton.clicked.connect(self.selectAllButtonPressed)
        self.ui.selectNoneButton.clicked.connect(self.selectNoneButtonPressed)
        self.ui.plotResetButton.clicked.connect(self.plotResetButtonPressed)

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

        # pointsavailable pressed
        self.ui.pointsAvailable.clicked.connect(self.pointsAvailablePressed)
        self.ui.pointsAvailable.itemSelectionChanged.connect(
            self.pointsAvailablePressed)
        self.ui.checkBoxCompare.clicked.connect(self.pointsAvailablePressed)

        # points
        self.ui.putPointsButton.setDisabled(True)
        self.ui.clearPointsButton.setDisabled(True)
        self.ui.putPointsButton.clicked.connect(self.putPointsButtonPressed)
        self.ui.clearPointsButton.clicked.connect(self.clearPointsButtonPressed)

        # filesAvailable
        self.ui.filesAvailable.clicked.connect(self.filesAvailablePressed)

        self.activeTab = 0

    def run(self):
        self.show()
        sys.exit(self.qt_app.exec_())

    def selectAllButtonPressed(self):
        for each in self.listBeaconItems.keys():
            self.listBeaconItems[each].setSelected(True)

    def selectNoneButtonPressed(self):
        for each in self.listBeaconItems.keys():
            self.listBeaconItems[each].setSelected(False)

    def resetDataButtonPressed(self):
        self.dataTime.clear()
        self.dataValue.clear()
        self.ui.filesAvailable.clear()
        self.ui.pointsAvailable.clear()
        self.ui.beaconsAvailable.clear()
        self.listFileItems.clear()
        self.listFileItemsRev.clear()
        self.listPointItems.clear()
        self.listPointItemsRev.clear()
        self.ui.putPointsButton.setDisabled(True)
        self.fileSelected = None

    def mergeButtonPressed(self):
        tempValue = {}
        tempTime = {}
        newFile = "Merged"
        tempValue[newFile] = {}
        tempTime[newFile] = {}
        self.hists.clear()
        self.hists = {}
        self.hists[newFile] = {}
        for file in self.dataValue.keys():
            for point in self.dataValue[file].keys():
                if not point in tempValue[newFile].keys():
                    tempValue[newFile][point] = {}
                    tempTime[newFile][point] = {}
                    self.hists[newFile][point] = {}

                for mac in self.dataValue[file][point].keys():
                    if not mac in self.hists[newFile].keys():
                        self.hists[newFile][point][mac] = []

                    if mac in tempValue[newFile][point].keys():
                        # buradaysak ust uste binen noktalar mevcut demek
                        for instance in self.dataValue[file][point][mac]:
                            tempValue[newFile][point][mac].append(instance)
                        for timeV in self.dataTime[file][point][mac]:
                            tempTime[newFile][point][mac].append(timeV)
                    else:
                        # kopyala
                        tempValue[newFile][point][mac] = \
                            self.dataValue[file][point][mac]
                        tempTime[newFile][point][mac] = \
                            self.dataTime[file][point][mac]

        for pts in self.hists[newFile].keys():
            for bea in self.hists[newFile][pts].keys():
                self.hists[newFile][pts][bea], bins = \
                    hist_from_data(tempValue[newFile][
                        pts][bea],(self.RssiMin, self.RssiMax))
                self.hists[newFile][pts][bea] = hist_normalize(
                        self.hists[newFile][pts][bea])


        self.resetDataButtonPressed()
        self.dataValue = tempValue
        self.dataTime = tempTime
        self.resetLists()

    def readDataButtonPressed(self):
        # self.ui.readDataButton.setText("Please Wait")
        self.dataFileNames = QtGui.QFileDialog.getOpenFileNames(self,
                                                              'Open file',
                                                              '../data',
                                                              'Log File ('
                                                              '*.csv)')
        bar = QtGui.QProgressDialog(self)
        bar.setWindowTitle("Please Wait")
        bar.setMinimum(0)
        bar.setMaximum(len(self.dataFileNames))
        bar.setCancelButton(None)
        progress = 0
        bar.open()
        bar.setValue(progress)

        for dataFile in self.dataFileNames:
            with open(dataFile, 'r') as f:
                self.dataValue[dataFile] = {}
                self.dataTime[dataFile] = {}
                self.hists[dataFile] = {}

                # readfile
                for line in f:
                    each = line.split(',')
                    point = (int(each[2]),int(each[3]))
                    time = float(each[0])
                    image = each[1].strip()
                    rssi = int(each[5])
                    mac = each[4].strip()
                    # if image.strip() == os.path.basename(str(self.imageFile)):
                    #     pass
                    # resim ayniysa topla falan
                    if point not in self.dataValue[dataFile].keys():
                        self.dataValue[dataFile][point] = {}
                        self.dataTime[dataFile][point] = {}
                        self.hists[dataFile][point] = {}

                    if mac not in self.dataValue[dataFile][point].keys():
                        self.dataValue[dataFile][point][mac] = []
                        self.dataTime[dataFile][point][mac] = []
                        self.hists[dataFile][point][mac] = []

                    if mac not in self.macColors.keys():
                        r,g,b = self.colorlines.pop()
                        self.macColors[mac] = QtGui.QColor(r,g,b)

                    self.dataValue[dataFile][point][mac].append(rssi)
                    self.dataTime[dataFile][point][mac].append(time)

                for pts in self.hists[dataFile].keys():
                    for bea in self.hists[dataFile][pts].keys():
                        self.hists[dataFile][pts][bea], bins = \
                            hist_from_data(self.dataValue[dataFile][
                                pts][bea],(self.RssiMin, self.RssiMax))
                        self.hists[dataFile][pts][bea] = hist_normalize(
                                self.hists[dataFile][pts][bea])


                if f:
                    print "Data file loaded "+ dataFile
                else:
                    print "Incompatible data file: " + dataFile

            # progressing bar
            progress += 1
            bar.setValue(progress)
        bar.close()

        self.resetLists()
        # self.ui.readDataButton.setText("Add Files")
        # print self.dataValue

    def resetLists(self):
        if len(self.dataValue) > 0:
            if self.imageFile:
                self.updateImage()
                self.ui.putPointsButton.setDisabled(False)

            for dataFile in sorted(self.dataValue.keys()):
                if dataFile not in self.listFileItems:
                    shortFile = str(os.path.basename(str(dataFile)))
                    itemFile = QtGui.QListWidgetItem("%s" %
                                        shortFile)
                    self.listFileItems[dataFile] = itemFile
                    self.listFileItemsRev[shortFile] = dataFile
                    self.ui.filesAvailable.addItem(itemFile)
        else:
            self.ui.putPointsButton.setDisabled(True)

    def filesAvailablePressed(self):
        if len(self.ui.filesAvailable.selectedItems()) > 0:
            self.fileSelected = self.listFileItemsRev[
                str(self.ui.filesAvailable.selectedItems()[0].text())]
            points = self.dataValue[self.fileSelected]
            self.ui.pointsAvailable.clear()
            self.listPointItems.clear()
            for point in points.keys():
                itemPoint = QtGui.QListWidgetItem("%s, %s" % (point[0], point[1]))
                self.ui.pointsAvailable.addItem(itemPoint)
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
                if len(beacons[mac]) > 1:
                    # f.setBold(True)
                    if self.ui.checkBoxCompare.isChecked():
                        itemBeacon = QtGui.QListWidgetItem("%s" % mac.strip())
                    else:
                        itemBeacon = QtGui.QListWidgetItem("%s (%s)" % (
                            mac.strip(), len(beacons[mac])))

                    itemBeacon.setTextColor(self.macColors[mac])
                    self.ui.beaconsAvailable.addItem(itemBeacon)
                    self.listBeaconItems[mac] = itemBeacon
                else:
                    if not self.ui.checkBoxCompare.isChecked():
                        itemBeacon = QtGui.QListWidgetItem("%s" % mac.strip())
                        itemBeacon.setTextColor(self.macColors[mac])
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

    def histogramButtonPressed(self,index):
        if len(self.ui.beaconsAvailable.selectedItems()) == 0:
            return

        self.hl[index].setXRange(self.RssiMin,self.RssiMax)

        self.hl[index].clear()
        if self.ui.checkBoxCompare.isChecked():
            hist = {}
            for each in self.ui.beaconsAvailable.selectedItems():
                mac = str(each.text())
                hist_temp = []
                weight_temp = []
                for point in self.pointsSelected:
                    hist_temp.append(self.hists[self.fileSelected]
                        [point][mac])
                    weight_temp.append(len(self.dataValue[self.fileSelected]
                        [point][mac]))
                hist[mac] = hist_merge(np.array(hist_temp),
                                                   np.array(weight_temp))
                self.hl[index].plot(self.rssiRange, hist[mac],
                         pen = {'color': self.macColors[mac]})
                self.hl[index].setYRange(0,1)

        else:
            for point in self.pointsSelected:
                for each in self.ui.beaconsAvailable.selectedItems():
                    mac = str(each.text()[0:17])
                    self.hl[index].plot(self.rssiRange,
                             self.hists[self.fileSelected][point][mac],
                             pen = {'color': self.macColors[mac]})
                    self.hl[index].setYRange(0,1)

    def timeSeriesButtonPressed(self):
        if len(self.ui.beaconsAvailable.selectedItems()) == 0:
            return
        self.pl.clear()
        xStart = None
        xEnd = None
        # pass to find the limits
        for each in self.ui.beaconsAvailable.selectedItems():
            mac = str(each.text()[0:17])
            for pts in self.pointsSelected:
                if not xStart or xStart > self.dataTime[
                    self.fileSelected][pts][mac][0]:
                    xStart = self.dataTime[self.fileSelected][pts][mac][0]
                if not xEnd or xEnd < self.dataTime[
                    self.fileSelected][pts][mac][-1]:
                    xEnd = self.dataTime[self.fileSelected][pts][mac][-1]

        self.ui.timeStart.setText(
            "Data start time: " +  str(time.ctime(xStart)))
        for each in self.ui.beaconsAvailable.selectedItems():
            mac = str(each.text()[0:17])
            for pts in self.pointsSelected:
                self.pl.plot(
                        [x/60.0 - xStart/60.0
                            for x in self.dataTime[self.fileSelected][pts][mac]],
                         self.dataValue[self.fileSelected][pts][mac],
                         pen = None,
                         symbolPen= {'color': self.macColors[mac]},
                         symbol='+',
                         symbolSize = 2)
                leftAxis = self.pl.getAxis('bottom')
                leftAxis.setTickSpacing(10, 1)
                self.pl.showGrid(x = True, y = True, alpha = 0.1)

    def histResetButtonPressed(self,index):
        self.hl[index].clear()

    def plotResetButtonPressed(self):
        self.ui.timeStart.clear()
        self.pl.clear()

    def resetImagePressed(self):
        self.imageScene.clear()
        self.imageFile = None
        self.ui.loadBeaconsButton.setDisabled(True)
        self.ui.noImageLabel.setVisible(True)

    def loadImagePressed(self):
        imageFile = QtGui.QFileDialog.getOpenFileName(self,
                                                      'Open file',
                                                      '../maps',
                                                      'Images (*.png *.xpm '
                                                      '*.jpg)' )
        if imageFile:
            with open(imageFile, 'r') as f:
                try:
                    self.imageFile = imageFile
                    self.ui.loadBeaconsButton.setDisabled(False)
                    self.updateImage()
                    # say that an image is loaded
                    print "Image loaded: " + imageFile
                    if self.fileSelected:
                        if len(self.dataValue[self.fileSelected]) > 0:
                            self.ui.putPointsButton.setDisabled(False)
                    f.close()
                except:
                    print "Problem with image file: " + self.imageFile
                    self.imageFile = None
                    self.ui.loadBeaconsButton.setDisabled(True)

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
        self.frame = QtGui.QImage(self.imageFile)
        self.frame = self.setOpacity(0.5)
        self.imageScene.clear()
        self.imageScene.addPixmap(QtGui.QPixmap.fromImage(self.frame))
        self.imageScene.setImageSize(self.frame.size())
        self.imageScene.update()
        self.ui.imageView.setScene(self.imageScene)
        self.placeBeacons()
        self.putPointsButtonPressed()
        if self.imageScene.latestPoint:
            self.imageScene.putTempEllipse()
        self.ui.noImageLabel.setVisible(False)

    def loadBeaconsButtonPressed(self):
        self.loadBeaconsFromFile()

    def loadBeaconsFromFile(self):
        bFile = QtGui.QFileDialog.getOpenFileName(self,
                                                  'Open file',
                                                  '../conf',
                                                  'Beacon Data (*.bea)')
        try:
            with open(bFile, 'r') as f:
                self.beaconsSet = json.load(f)
                self.updateImage()
                self.beaconFile = bFile
                print "Beacons loaded: " + self.beaconFile
                f.close()
        except:
            print "Incompatible File: " + bFile
            # self.beaconFile = None

    def placeBeacons(self):
        if self.imageFile and self.beaconsSet:
            self.ui.clearBeaconsButton.setDisabled(False)
            # colorize item list
            for mac in self.beaconsSet.keys():
                    self.imageScene.addPoint(
                            QtCore.QPoint(self.beaconsSet[mac][0][0],
                             self.beaconsSet[mac][0][1]),
                            ".:" + str(mac[-5:]),
                            QtGui.QColor(
                                self.beaconsSet[mac][1]
                            ))


    def clearBeaconsButtonPressed(self):
        self.beaconsSet.clear()
        self.ui.clearBeaconsButton.setDisabled(True)
        self.updateImage()

    def putPointsButtonPressed(self):
        if self.fileSelected:
            for each in self.dataValue[self.fileSelected].keys():
                if self.listPointItems[each].isSelected():
                    self.imageScene.addPoint(QtCore.QPoint(
                                            each[0],
                                            each[1]),
                                            str((each[0], each[1])),
                                            QtGui.QColor(0,0,0))
                else:
                    self.imageScene.addPoint(QtCore.QPoint(
                                            each[0],
                                            each[1]),
                                            str((each[0], each[1])),
                                            QtGui.QColor(255,255,255))

            if len(self.dataValue[self.fileSelected].keys()) > 0:
                self.ui.clearPointsButton.setDisabled(False)

    def clearPointsButtonPressed(self):
        self.updateImage()
        self.ui.clearPointsButton.setDisabled(True)


def main():

    app = btViewerGui()
    app.run()

if __name__ == '__main__':
    main()
