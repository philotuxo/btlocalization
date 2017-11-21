#!/usr/bin/python
# -*- coding: utf-8 -*-

import Queue
import signal
import sys, os
from PyQt4 import QtGui
from PyQt4 import QtCore
import dbus
from lib.btLocator_ui import Ui_BeaconLoc
from lib.histogram_visuals import *
from lib.bleThread import BluetoothThread
from lib.btQtCore import btImageScene, signal_handler
from btLivePlot import btLivePlotGui
import time

class LocatorImageScene(btImageScene):
    def __init__(self):
        QtGui.QGraphicsScene.__init__(self)
        self.circleRadius = 5
        self.latestPoint = None
        self.newEllipse = None
        self.setBeaconState = False
        self.setPointState = False

    def mousePressEvent(self, event):
        self.latestPoint = QtCore.QPoint(event.scenePos().x(),
                                         event.scenePos().y())
        if self.setPointState:
            self.addTempPoint(self.latestPoint)

    def addTempPoint(self, point):

        if self.newEllipse:
            self.removeItem(self.newEllipse)
        self.newEllipse = QtGui.QGraphicsEllipseItem(
                        point.x() - self.circleRadius,
                        point.y() - self.circleRadius,
                        2* self.circleRadius,
                        2* self.circleRadius)
        br = QtGui.QBrush()
        br.setStyle(1) # RadialGradient pattern
        br.setColor(QtGui.QColor(0,255,0))
        self.newEllipse.setBrush(br)
        if point.x() > self.circleRadius \
                and point.y() > self.circleRadius \
                and point.x() < self.sizeX - self.circleRadius \
                and point.y() < self.sizeY - self.circleRadius:
            self.addItem(self.newEllipse)
        else:
            self.newEllipse = None


class btLocatorGui(btLivePlotGui):
    def __init__(self, btQueue, dcQueue):
        # stateoff
        self.qt_app = QtGui.QApplication(sys.argv)
        QtGui.QWidget.__init__(self, None)

        # create the main ui
        self.ui = Ui_BeaconLoc()
        self.ui.setupUi(self)
        self.imageScene = LocatorImageScene()
        # get the adapter first
        self.rssiLimits = (-115, 15)

        # start timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updatePlotByTimeout)

        # update every 100 ms
        self.timer.start(100)

        # start time
        self.t = QtCore.QTime()
        self.t.start()
        self.startTime = time.time()


        # get a dictionary for bt data
        self.btPlotItems = {}
        self.btSelectedItem = None
        self.btQueue = btQueue

        # plotting
        self.pl = self.ui.plotView.addPlot()
        self.hl = self.ui.histView.addPlot()
        self.hl.setYRange(0,1)
        self.pl.setYRange(self.rssiLimits[0], self.rssiLimits[1])
        self.pl.showGrid(alpha=.5, x=True, y = True)
        self.pl.getAxis("bottom").setTickSpacing(10,1)
        self.curves = {}
        self.ydata = {}
        self.xdata = {}
        self.timeBuffer = 20


        self.colorlines = colorlines
        self.colorlines.reverse()
        self.lineindex = 0
        self.legend = self.pl.addLegend()
        self.ui.selectAllButton.clicked.connect(self.selectAllButtonPressed)
        self.ui.selectNoneButton.clicked.connect(self.selectNoneButtonPressed)
        self.ui.selectResetButton.clicked.connect(self.selectResetButtonPressed)
        self.ui.plotResetButton.clicked.connect(self.plotResetButtonPressed)

        # select list click
        self.ui.selectBeaconList.clicked.connect(self.selectBeaconListPressed)

        # histogram
        self.histograms = {}
        # self.ui.histSelectButton.clicked.connect(self.histSelectButtonPressed)
        self.ui.histResetButton.clicked.connect(self.histResetButtonPressed)
        self.rssiRange = np.arange(self.rssiLimits[0], self.rssiLimits[1], 1)

        # image load
        self.imageFile = None
        self.ui.loadImageButton.clicked.connect(self.loadImagePressed)
        self.ui.resetImageButton.clicked.connect(self.resetImagePressed)

        # save button pressed
        self.beaconFile = None
        self.ui.saveBeaconsButton.clicked.connect(self.saveBeaconsPressed)
        self.ui.saveBeaconsAsButton.clicked.connect(self.saveBeaconsAsPressed)
        self.ui.loadBeaconsButton.clicked.connect(self.loadBeaconsPressed)
        self.ui.clearBeaconsButton.clicked.connect(self.clearBeaconsPressed)

        # collect file initialize
        self.collectFile = None
        self.collectStart = None
        self.collectDuration = None

        # locator key pressed
        self.ui.placeBeaconButton.clicked.connect(self.beaconSetPressed)

        # ok button pressed
        self.ui.beaconOkButton.clicked.connect(self.beaconOkButtonPressed)
        self.ui.beaconRemoveButton.clicked.connect(
            self.beaconRemoveButtonPressed)
        self.ui.beaconCancelButton.clicked.connect(
            self.beaconCancelButtonPressed)

        # data collect button pressed
        self.ui.dataCollectButton.clicked.connect(self.dataCollectPressed)
        self.ui.dataStartButton.clicked.connect(self.dataCollectStartPressed)
        self.ui.dataCancelButton.clicked.connect(self.dataCollectCancelPressed)
        self.ui.durationCheckBox.clicked.connect(self.durationCheckBoxPressed)
        self.ui.dataOpenFileButton.clicked.connect(
            self.dataOpenFileButtonPressed)
        self.ui.dataResetFileButton.clicked.connect(
            self.dataResetFileButtonPressed)

        # data process button pressed
        self.dataFileName = None
        self.ui.loggedPointsButton.clicked.connect(self.loggedPointsButtonPressed)
        self.ui.clearPointsButton.clicked.connect(self.clearDataButtonPressed)

        # adapter selection
        self.adapters = []
        self.generateAdaptersBox()
        self.ui.deviceSelectBox.currentIndexChanged.connect(self.adapterChanged)

        # previously set beacons
        self.beaconsSet = {}

        # previously collected data
        self.collectionSet = {}

        # data collect message queue
        self.dcQueue = dcQueue
        self.confBegin()

        # dps
        self.lastDataTime = []

        # check flag if update running
        self.updateRunning = False

    def getAdapters(self):

        BUS_NAME = 'org.bluez'
        SERVICE_NAME = 'org.bluez'
        ADAPTER_INTERFACE = SERVICE_NAME + '.Adapter1'

        bus = dbus.SystemBus()
        manager = dbus.Interface(bus.get_object(BUS_NAME, '/'),
                                 'org.freedesktop.DBus.ObjectManager')

        objects =  manager.GetManagedObjects()

        adapters = []

        for path, interfaces in objects.iteritems():
            adapter = interfaces.get(ADAPTER_INTERFACE)
            if adapter is None:
                continue
            adapters.append(
                (str(adapter.get(u'Address')), str(adapter.get(u'Alias')))
            )
        return adapters

    def closeEvent(self,event):
        # close gracefully
        self.dcQueue.put(("QUIT",None))
        self.close()

    def generateAdaptersBox(self):
        adapters = self.getAdapters()
        self.ui.deviceSelectBox.addItem("Select a BLE device")
        self.adapters.append(None)

        counter = 1

        for adapter in adapters:
            self.adapters.append(adapter[0])
            self.ui.deviceSelectBox.addItem("%s: %s" % (adapter[0], adapter[1]))
            counter += 1

    def adapterChanged(self):
        # adapter degistirilirse bunu bluetooth threadine bildir
        self.dcQueue.put(
            ("BDADDR",
             self.adapters[self.ui.deviceSelectBox.currentIndex()]
            )
        )
        self.dcQueue.put(("START", None))

    def confBegin(self):
        # vars
        self.imageScene.setBeaconState = False
        self.imageScene.setPointState = False
        self.imageScene.newEllipse = None
        self.imageScene.latestPoint = None
        self.dataCollectState = False

        # image button enabled
        self.ui.loadImageButton.setDisabled(False)

        # warning visible
        self.ui.beaconWarningLabel.setVisible(False)
        self.ui.labelSelected.setVisible(False)

        # beacon locate invisible
        self.ui.selectInstructionLabel.setDisabled(False)
        self.ui.beaconOkButton.setVisible(False)
        self.ui.beaconRemoveButton.setVisible(False)
        self.ui.beaconCancelButton.setVisible(False)
        self.ui.instructionLabel.setVisible(False)
        self.ui.saveBeaconsAsButton.setDisabled(True)
        self.ui.saveBeaconsButton.setDisabled(True)
        self.ui.clearBeaconsButton.setDisabled(True)

        # collect data visible
        self.ui.dataCollectButton.setDisabled(False)
        self.ui.dataStartButton.setVisible(False)
        self.ui.dataCancelButton.setVisible(False)
        self.ui.labelCollect.setVisible(False)
        self.ui.dataOpenFileButton.setDisabled(False)
        if self.collectFile:
            self.ui.dataOpenedFileLabel.setText("File: " +
                                    os.path.basename(str(self.collectFile)))
            self.ui.dataOpenedFileLabel.setStyleSheet('color: green')
            self.ui.dataResetFileButton.setDisabled(False)
        else:
            self.ui.dataOpenedFileLabel.setText("No File Selected.")
            self.ui.dataOpenedFileLabel.setStyleSheet('color: red')
            self.ui.dataResetFileButton.setDisabled(True)
        if self.collectDuration:
            self.ui.durationSpinBox.setValue(self.collectDuration)

        if len(self.ui.selectBeaconList.selectedIndexes()) > 0:
            self.ui.placeBeaconButton.setVisible(True)
            self.ui.placeBeaconButton.setDisabled(False)
        else:
            self.ui.placeBeaconButton.setVisible(False)

        self.ui.durationCheckBox.setVisible(False)
        self.ui.durationLeftTime.setVisible(False)
        self.ui.durationSpinBox.setVisible(False)
        if self.ui.durationCheckBox.isChecked():
            self.ui.durationSpinBox.setDisabled(False)
            self.ui.durationLeftTime.setDisabled(False)
        else:
            self.ui.durationSpinBox.setDisabled(True)
            self.ui.durationLeftTime.setDisabled(True)

        # process dataFileButton
        self.ui.loggedPointsButton.setDisabled(True)
        self.ui.clearPointsButton.setDisabled(True)
        self.ui.loadBeaconsButton.setDisabled(True)

        # beacon list enabled
        self.ui.selectBeaconList.setDisabled(False)

        # warning invisible
        self.ui.pointNotPut.setVisible(False)

        if len(self.collectionSet) > 0:
            self.ui.clearPointsButton.setDisabled(False)
        else:
            self.ui.clearPointsButton.setDisabled(True)

        if len(self.beaconsSet) > 0:
            self.ui.clearBeaconsButton.setDisabled(False)
            self.ui.saveBeaconsAsButton.setDisabled(False)
        else:
            self.ui.clearBeaconsButton.setDisabled(True)
            self.ui.saveBeaconsAsButton.setDisabled(True)

        if self.imageFile:
            self.ui.noImageLabel.setVisible(False)
            self.ui.loggedPointsButton.setDisabled(False)
            self.ui.loadBeaconsButton.setDisabled(False)
            self.ui.resetImageButton.setDisabled(False)
        else:
            self.ui.noImageLabel.setVisible(True)
            self.ui.loggedPointsButton.setDisabled(True)
            self.ui.loadBeaconsButton.setDisabled(True)
            self.ui.resetImageButton.setDisabled(True)

    def run(self):
        self.show()
        self.qt_app.exec_()


    def confImageLoaded(self):
        # vars
        self.imageScene.setBeaconState = False
        self.imageScene.setPointState = False
        self.imageScene.newEllipse = None
        self.imageScene.latestPoint = None

        # others
        self.confBegin()
        self.ui.noImageLabel.setVisible(False)
        self.ui.beaconWarningLabel.setVisible(False)

        # this
        self.ui.loadImageButton.setDisabled(False)
        self.ui.loggedPointsButton.setDisabled(False)
        self.ui.loadBeaconsButton.setDisabled(False)

        if len(self.collectionSet) > 0:
            self.ui.clearPointsButton.setDisabled(False)
        else:
            self.ui.clearPointsButton.setDisabled(True)

        if len(self.beaconsSet) > 0:
            if self.beaconFile:
                self.ui.saveBeaconsButton.setDisabled(False)
            else:
                self.ui.saveBeaconsButton.setDisabled(True)
            self.ui.saveBeaconsAsButton.setDisabled(False)
            self.ui.clearBeaconsButton.setDisabled(False)
        else:
            self.ui.saveBeaconsAsButton.setDisabled(True)
            self.ui.clearBeaconsButton.setDisabled(True)


    def confSelectCollectPoint(self):
        # vars
        selectedMAC = []
        for each in self.btPlotItems.keys():
            if self.btPlotItems[each][1].isSelected():
                selectedMAC.append(each)
        self.dataCollectState = True
        self.imageScene.setPointState = False
        self.dcQueue.put(("FILE",
                         os.path.basename(str(self.imageFile)),
                         self.collectFile,
                         self.imageScene.latestPoint.x(),
                         self.imageScene.latestPoint.y()
                        ))

        self.dcQueue.put(("START", selectedMAC))

        if self.ui.durationCheckBox.isChecked() and \
               self.ui.durationSpinBox.value() > 0:
            self.collectStart = self.t.elapsed()

        # this
        self.ui.labelCollect.setStyleSheet('color: green')
        self.ui.labelCollect.setText(
            "Collecting at " +
            str(int(self.imageScene.latestPoint.x())) +
            ", " +
            str(int(self.imageScene.latestPoint.y()))
        )
        self.ui.dataCancelButton.setVisible(False)
        self.ui.dataStartButton.setText("End")

        # others
        self.ui.loadImageButton.setDisabled(True)
        self.ui.loggedPointsButton.setDisabled(True)
        self.ui.loadBeaconsButton.setDisabled(True)
        br = QtGui.QBrush()
        br.setStyle(1)
        br.setColor(QtGui.QColor(255,255,0))
        self.imageScene.newEllipse.setBrush(br)
        newText = QtGui.QGraphicsSimpleTextItem("Collecting!")

        newText.setFont(QtGui.QFont('Mono',8))
        newText.setParentItem(self.imageScene.newEllipse)
        newText.setPos(
            self.imageScene.latestPoint.x() - 35,
            self.imageScene.latestPoint.y() + 10
        )
        newText.setBrush(br)


    def confSetBeacon(self):
        # vars
        self.imageScene.setBeaconState = True
        self.imageScene.setPointState = True

        # this
        self.ui.placeBeaconButton.setVisible(False)
        # self.ui.histSelectButton.setVisible(False)
        self.ui.beaconOkButton.setVisible(True)
        self.ui.beaconRemoveButton.setVisible(True)
        self.ui.beaconCancelButton.setVisible(True)
        self.ui.instructionLabel.setVisible(True)
        self.ui.selectBeaconList.setDisabled(True)
        self.ui.labelSelected.setText("Beacon MAC: " +
            self.ui.selectBeaconList.selectedItems()[0].text()
        )
        self.ui.labelSelected.setVisible(True)
        self.ui.beaconWarningLabel.setVisible(False)

        # others
        self.ui.dataCollectButton.setDisabled(True)
        self.ui.dataStartButton.setVisible(False)
        self.ui.dataCancelButton.setVisible(False)
        self.ui.loadImageButton.setDisabled(True)
        self.ui.resetImageButton.setDisabled(True)
        self.ui.saveBeaconsButton.setDisabled(True)
        self.ui.saveBeaconsAsButton.setDisabled(True)
        self.ui.clearBeaconsButton.setDisabled(True)
        self.ui.loggedPointsButton.setDisabled(True)
        self.ui.clearPointsButton.setDisabled(True)
        self.ui.loadBeaconsButton.setDisabled(True)


    def confEndCollect(self):
        self.ui.labelCollect.setText("Collecting completed.")
        self.ui.labelCollect.setStyleSheet('color: green')
        self.ui.labelCollect.setVisible(True)

    def confDataCollect(self):
        # vars
        self.imageScene.setPointState = True

        # others
        self.ui.placeBeaconButton.setDisabled(True)
        self.ui.resetImageButton.setDisabled(True)
        self.ui.saveBeaconsButton.setDisabled(True)
        self.ui.saveBeaconsAsButton.setDisabled(True)
        self.ui.clearBeaconsButton.setDisabled(True)
        self.ui.loggedPointsButton.setDisabled(True)
        self.ui.clearPointsButton.setDisabled(True)
        self.ui.loadBeaconsButton.setDisabled(True)
        self.ui.loadImageButton.setDisabled(True)
        self.ui.beaconOkButton.setVisible(False)
        self.ui.beaconRemoveButton.setVisible(False)
        self.ui.beaconCancelButton.setVisible(False)
        self.ui.instructionLabel.setVisible(False)
        self.ui.selectBeaconList.setDisabled(True)
        self.ui.labelSelected.setVisible(False)
        self.ui.selectInstructionLabel.setDisabled(True)

        # this
        self.ui.dataStartButton.setText("Start")
        self.ui.dataStartButton.setVisible(True)
        self.ui.dataCollectButton.setDisabled(True)
        self.ui.dataCancelButton.setVisible(True)
        self.ui.labelCollect.setStyleSheet('color: black')
        self.ui.labelCollect.setText("Put a point on the map.")
        self.ui.labelCollect.setVisible(True)
        self.ui.durationCheckBox.setVisible(True)
        self.ui.durationSpinBox.setVisible(True)
        self.ui.durationLeftTime.setVisible(True)
        self.ui.dataResetFileButton.setDisabled(True)
        self.ui.dataOpenFileButton.setDisabled(True)

    def selectBeaconListPressed(self):
        if len(self.ui.selectBeaconList.selectedIndexes()) > 0 and \
                self.ui.selectBeaconList.isEnabled():
            self.ui.placeBeaconButton.setVisible(True)
            self.ui.placeBeaconButton.setDisabled(False)

    def loggedPointsButtonPressed(self):
        self.ui.loggedPointsButton.setText("Processing")
        self.dataFileName = QtGui.QFileDialog.getOpenFileName(self,
                                                              'Open file',
                                                              '../data',
                                                              'Log File ('
                                                              '*.csv)')
        self.collectionSet.clear()
        try:
            with open(self.dataFileName, 'r') as f:
                for line in f:
                    each = line.split(',')
                    if each[1].strip() == os.path.basename(str(self.imageFile)):
                        try:
                            self.collectionSet[(int(each[2]),int(each[3]))] += 1
                        except KeyError:
                            self.collectionSet[(int(each[2]),int(each[3]))] = 1

                print "Data file loaded "+ self.dataFileName
                self.updateImage()
        except:
            print "Incompatible data file: " + self.dataFileName

        self.ui.loggedPointsButton.setText("Logged Points")

    def clearDataButtonPressed(self):
        self.collectionSet.clear()
        self.updateImage()

    def dataCollectStartPressed(self):
        if self.dataCollectState:
            # end collecting
            self.updateImage()
            self.confBegin()
            self.confEndCollect()
            self.dataCollectState = False
            self.collectStart = None
            self.dcQueue.put(("START", None ))
        else:
            if self.imageScene.latestPoint:
                # start collecting if everything is set
                self.confSelectCollectPoint()
            else:
                # we need a point
                self.ui.labelCollect.setStyleSheet('color: red')
                self.ui.labelCollect.setText("No point selected!")
                self.ui.labelCollect.setVisible(True)

        self.collectDuration = self.ui.durationSpinBox.value()
        self.durationLeft_old = self.collectDuration


    def dataCollectCancelPressed(self):
        if self.imageScene.newEllipse:
            self.imageScene.removeItem(self.imageScene.newEllipse)
        self.confBegin()

    def dataCollectPressed(self):
        if self.imageFile:
            if self.collectFile:
                self.confDataCollect()
            else:
                self.confBegin()
                self.ui.dataOpenedFileLabel.setStyleSheet('color: red')
                self.ui.dataOpenedFileLabel.setText("No file loaded!")
                self.ui.dataOpenedFileLabel.setVisible(True)
        else:
            # no image
            self.ui.labelCollect.setStyleSheet('color: red')
            self.ui.labelCollect.setText("No image loaded!")
            self.ui.labelCollect.setVisible(True)

    def dataResetFileButtonPressed(self):
        self.collectFile = None
        self.ui.dataOpenedFileLabel.setText("No File Selected.")
        self.ui.dataOpenedFileLabel.setStyleSheet('color: red')
        self.ui.dataResetFileButton.setDisabled(True)

    def dataOpenFileButtonPressed(self):
        fileDialog = QtGui.QFileDialog()
        # fileDialog.setDefaultSuffix("csv")
        cFile = fileDialog.getSaveFileName(self,
                    'Save file',
                    '../data/untitled.csv',
                    'Log Data '
                    '(*.csv);; All Files '
                    '(*.*)',
                    options = QtGui.QFileDialog.DontConfirmOverwrite)
        if cFile:
            self.collectFile = cFile
            self.ui.dataOpenedFileLabel.setStyleSheet('color: green')
            self.ui.dataOpenedFileLabel.setText("File: " +
                                    os.path.basename(str(self.collectFile)))
            self.ui.dataResetFileButton.setDisabled(False)
        else:
            self.collectFile = None
            self.ui.dataOpenedFileLabel.setText("No File Selected.")
            self.ui.dataOpenedFileLabel.setStyleSheet('color: red')
            self.ui.dataResetFileButton.setDisabled(True)


    def durationCheckBoxPressed(self):
        if self.ui.durationCheckBox.isChecked():
            self.ui.durationSpinBox.setDisabled(False)
            self.ui.durationLeftTime.setDisabled(False)
        else:
            self.ui.durationSpinBox.setDisabled(True)
            self.ui.durationLeftTime.setDisabled(True)

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

    def saveBeaconsToFile(self, overwrite):
        if not overwrite:
            self.beaconFile = QtGui.QFileDialog.getSaveFileName(self,
                                                                'Save file',
                                                                '../conf',
                                                                'Beacon Data '
                                                                '(*.bea)')
        with open(self.beaconFile, 'w') as f:
            print "Writing to file: "  + self.beaconFile
            # generate a tempFile

            json.dump(self.beaconsSet, f)
            self.ui.pointNotPut.setText("Beacon placements saved to " +
                                           os.path.basename(str(
                                               self.beaconFile)) +
                                           "."
            )
            self.ui.pointNotPut.setStyleSheet('color: green')
            self.ui.pointNotPut.setVisible(True)

    def placeBeacons(self):
        if self.imageFile:
            # colorize item list
            for each in self.btPlotItems.keys():
                self.btPlotItems[str(each)][2].setTextColor(
                    QtGui.QColor(self.btPlotItems[each][3]))
                if each in self.beaconsSet.keys():
                    self.btPlotItems[str(each)][2].setBackgroundColor(
                    QtGui.QColor(0,0,0))
                else:
                    self.btPlotItems[str(each)][2].setBackgroundColor(
                    QtGui.QColor(255,255,255))

            for each in self.beaconsSet:
                self.imageScene.addPoint(QtCore.QPoint(
                                        self.beaconsSet[each][0][0],
                                        self.beaconsSet[each][0][1]),
                                        ".:" + str(each[-5:]),
                                        QtGui.QColor(
                                            self.beaconsSet[each][1]
                                        ))

            for each in self.collectionSet:
                self.imageScene.addPoint(QtCore.QPoint(
                                        each[0],
                                        each[1]),
                                        str(each),
                                        QtGui.QColor(0,255,255))

    def resetImagePressed(self):
        self.frame = QtGui.QImage(self.imageFile)
        self.imageScene.clear()
        self.imageScene.addPixmap(QtGui.QPixmap.fromImage(self.frame))
        self.imageScene.setImageSize(self.frame.size())
        self.imageScene.update()
        self.ui.imageView.setScene(self.imageScene)


    def loadImagePressed(self):
        imageFile = QtGui.QFileDialog.getOpenFileName(self,
                                                      'Open file',
                                                      '../maps',
                                                      'Images (*.png *.xpm '
                                                      '*.jpg)' )
        with open(imageFile, 'r') as f:
            try:
                self.imageFile = imageFile
                self.updateImage()
                # say that an image is loaded
                # self.confImageLoaded()
                print "Image loaded: " + imageFile
                f.close()
            except:
                print "Problem with image file: " + self.imageFile
                self.imageFile = None


    def updateImage(self):
        self.frame = QtGui.QImage(self.imageFile)
        self.imageScene.clear()
        self.imageScene.addPixmap(QtGui.QPixmap.fromImage(self.frame))
        self.imageScene.setImageSize(self.frame.size())
        self.imageScene.update()
        self.ui.imageView.setScene(self.imageScene)
        self.placeBeacons()
        self.confImageLoaded()

    def beaconSetPressed(self):
        if self.imageFile:
            self.confSetBeacon()
        else:
            self.ui.beaconWarningLabel.setStyleSheet('color: red')
            self.ui.beaconWarningLabel.setText('No image loaded!')
            self.ui.beaconWarningLabel.setVisible(True)

    def saveBeaconsPressed(self):
        self.saveBeaconsToFile(True)

    def saveBeaconsAsPressed(self):
        self.saveBeaconsToFile(False)

    def loadBeaconsPressed(self):
        self.loadBeaconsFromFile()

    def clearBeaconsPressed(self):
        self.beaconsSet.clear()
        self.collectionSet.clear()
        self.updateImage()

    def beaconOkButtonPressed(self):
        if self.imageScene.latestPoint:
            self.beaconsSet[
                str(self.ui.selectBeaconList.selectedItems()[0].text())] = (
                (self.imageScene.latestPoint.x(),
                 self.imageScene.latestPoint.y()
                ),
                self.btPlotItems[
                    str(self.ui.selectBeaconList.selectedItems()[0].text())][3]
                )


            # self.confImageLoaded()

            # clear items
            self.updateImage()
        else:
            self.ui.pointNotPut.setStyleSheet('color: red')
            self.ui.pointNotPut.setText("Point not put!")
            self.ui.pointNotPut.setVisible(True)

    def beaconRemoveButtonPressed(self):
        if str(self.ui.selectBeaconList.selectedItems()[0].text()) \
                in self.beaconsSet.keys():
            del self.beaconsSet[
                str(self.ui.selectBeaconList.selectedItems()[0].text())
            ]
            # self.confImageLoaded()
            self.updateImage()
        else:
            self.ui.pointNotPut.setText("Beacon not set!")
            self.ui.pointNotPut.setVisible(True)


    def beaconCancelButtonPressed(self):
        # self.confImageLoaded()
        self.updateImage()

    def selectAllButtonPressed(self):
        for each in self.btPlotItems.keys():
            self.btPlotItems[each][1].setSelected(True)

    def selectNoneButtonPressed(self):
        for each in self.btPlotItems.keys():
            self.btPlotItems[each][1].setSelected(False)

    def selectResetButtonPressed(self):
        for mac in self.btPlotItems.keys():
            self.btPlotItems[mac][1] = None
            self.btPlotItems[mac][2] = None
            self.ui.btPlotList.clear()
            self.ui.selectBeaconList.clear()

    def histResetButtonPressed(self):
        self.histograms.clear()
        self.hl.clear()
        self.hl.setYRange(0,1)

    def plotResetButtonPressed(self):
        self.ydata.clear()
        self.curves.clear()
        self.legend.scene().removeItem(self.legend)
        self.legend = self.pl.addLegend()
        self.pl.clear()
        self.pl.setYRange(self.rssiLimits[0], self.rssiLimits[1])

def main():

    # data collect message queue
    dcQueue = Queue.Queue()

    # bluetooth thread
    btQueue = Queue.Queue()

    # define the bluetooth thread
    btThread = BluetoothThread("BluetoothThread", dcQueue, btQueue)
    btThread.setDaemon(True)
    btThread.start()

    app = btLocatorGui(btQueue, dcQueue)
    app.run()

    btThread.join()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()
