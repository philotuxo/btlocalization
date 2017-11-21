#!/usr/bin/python
# -*- coding: utf-8 -*-
import Queue
import signal
import sys
from PyQt4 import QtGui, Qt
import dbus
from lib.btLivePlot_ui import Ui_BeaconLivePlot
from lib.histogram_visuals import *
from lib.bleThread import BluetoothThread
import time
from lib.btQtCore import signal_handler


class btLivePlotGui(QtGui.QMainWindow):
    def __init__(self, btQueue, dcQueue):
        # stateoff
        self.qt_app = QtGui.QApplication(sys.argv)
        QtGui.QWidget.__init__(self, None)

        # create the main ui
        self.ui = Ui_BeaconLivePlot()
        self.ui.setupUi(self)
        # get the adapter first
        self.rssiLimits = (-110, 10)

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
        self.ui.selectBeaconList = None

        # histogram
        self.histograms = {}
        # self.ui.histSelectButton.clicked.connect(self.histSelectButtonPressed)
        self.ui.histResetButton.clicked.connect(self.histResetButtonPressed)
        self.rssiRange = np.arange(self.rssiLimits[0], self.rssiLimits[1], 1)

        # adapter selection
        self.adapters = []
        self.generateAdaptersBox()
        self.ui.deviceSelectBox.currentIndexChanged.connect(self.adapterChanged)

        # data collect message queue
        self.dcQueue = dcQueue

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

        if self.ui.deviceSelectBox.currentIndex() > 0:
            self.dcQueue.put(
                ("BDADDR",
                 self.adapters[self.ui.deviceSelectBox.currentIndex()]
                )
            )
            self.dcQueue.put(("START", None))
        else:
            self.dcQueue.put(("END", None))

    def run(self):
        self.show()
        self.qt_app.exec_()

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

    def updateDataShow(self, mac, rssi, txValue):
        now = time.time()
        n = len(self.lastDataTime)

        if  n > 8:
            self.lastDataTime.pop(0)
        self.lastDataTime.append(now)
        diff = now - self.lastDataTime[0]
        if not diff == 0:
            self.ui.dps.setText("DPS: %s hz" % round(float(n)/diff,1))

        if self.ui.collectDataShow.count() > 8:
            self.ui.collectDataShow.takeItem(0)
        temp = QtGui.QListWidgetItem(str(mac) +
                                     " | " + str(rssi) +
                                     " | " + str(txValue))
        temp.setTextColor(QtGui.QColor(self.btPlotItems[mac][3]))
        self.ui.collectDataShow.addItem(temp)

    def updatePlotByTimeout(self):
        # if not the function is already running
        if self.updateRunning:
            return
        else:
            self.updateRunning = True

        elapsed_time = self.t.elapsed()/1000.0
        self.pl.setXRange(elapsed_time - self.timeBuffer, elapsed_time)
        self.ui.labelTime.setText(str(round(elapsed_time,1)))

        for mac in self.xdata.keys():
            # print len(self.xdata[mac])
            index = 0
            try:
                while self.xdata[mac][index] < elapsed_time - self.timeBuffer:
                    index += 1
                self.xdata[mac] = self.xdata[mac][index:]
                self.ydata[mac] = self.ydata[mac][index:]
            except IndexError:
                pass

        if self.btQueue.qsize() > 0:
            while self.btQueue.qsize() > 0:
                data = self.btQueue.get()

                t = data[0]
                mac = data[1]
                rssi = data[2]
                uuid = data[3]
                major = data[4]
                minor = data[5]
                txValue = data[6]
                self.updateListBoxes(mac, uuid, major, minor)
                dataTime = t - self.startTime
                self.updateDataShow(mac,rssi,txValue)

                # prune here
                # if we want to visualize the beacon
                if self.btPlotItems[mac][1].isSelected():
                    # create y data
                    try:
                        self.ydata[mac] = np.append(self.ydata[mac],rssi)
                    except KeyError:
                        self.ydata[mac] = np.array([rssi])

                    try:
                        self.xdata[mac] = np.append(self.xdata[mac],dataTime)
                    except KeyError:
                        self.xdata[mac] = np.array([dataTime])

                        tempcurve = self.pl.plot(self.xdata[mac],
                                             self.ydata[mac],
                                             pen=None,
                                             symbol = '+',
                                             symbolSize = 3,
                                             symbolPen = {'color':QtGui.QColor(
                                               self.btPlotItems[mac][3])},
                                             symbolBrush = None,
                                             grid=128)

                    try:
                        self.curves[mac].setData(
                                self.xdata[mac], self.ydata[mac])
                    except KeyError:
                        self.curves[mac] = tempcurve
                        self.lineindex = self.lineindex + 1
                        self.legend.addItem(tempcurve, "%s" % (mac[-5:]))
                        self.curves[mac].setData(
                                self.xdata[mac], self.ydata[mac])

                    try:
                        self.histograms[mac][rssi - self.rssiLimits[0]] = \
                            self.histograms[mac][rssi - self.rssiLimits[0] ] + 1
                    except KeyError:
                        self.histograms[mac] = np.zeros(self.rssiLimits[1] -
                                                        self.rssiLimits[0])
                        self.histograms[mac][rssi - self.rssiLimits[0]] = \
                            self.histograms[mac][rssi - self.rssiLimits[0] ] + 1

                    self.hl.clear()
                    for each in self.histograms.keys():
                        self.hl.plot(self.rssiRange,
                        self.histograms[each]/float(sum(self.histograms[each])),
                                 pen = {'color': QtGui.QColor(
                                     self.btPlotItems[each][3])})

        # Leave the flag
        self.updateRunning = False

    def updateListBoxes(self, mac, uuid, major, minor):
        # update the List Box

        if not mac in self.btPlotItems.keys():
            itemPlot = QtGui.QListWidgetItem("%s | %s... | %s | %s "
                                  % (mac, uuid[0:8], major, minor))

            itemSelect = QtGui.QListWidgetItem("%s" % (mac))
            # get new color for the beacon
            r,g,b = self.colorlines.pop()
            self.btPlotItems[mac] = [mac,
                                     itemPlot,
                                     itemSelect,
                                     rgb2int((r,g,b))]
            itemPlot.setTextColor(QtGui.QColor(self.btPlotItems[mac][3]))

            itemSelect.setTextColor(QtGui.QColor(self.btPlotItems[mac][3]))
            if not self.ui.selectBeaconList == None:
                if mac in self.beaconsSet.keys():
                    itemSelect.setBackgroundColor(
                    QtGui.QColor(0,0,0))
                else:
                    itemSelect.setBackgroundColor(
                    QtGui.QColor(255,255,255))
                self.ui.selectBeaconList.addItem(itemSelect)
            self.ui.btPlotList.addItem(itemPlot)
            return

        if not self.btPlotItems[mac][1]:
            itemPlot = QtGui.QListWidgetItem("%s | %s... | %s | %s "
                                    % (mac, uuid[0:8], major, minor))
            itemPlot.setTextColor(QtGui.QColor(self.btPlotItems[mac][3]))
            self.btPlotItems[mac][1] = itemPlot
            self.ui.btPlotList.addItem(itemPlot)

        if not self.btPlotItems[mac][2]:
            itemSelect = QtGui.QListWidgetItem("%s" % (mac))
            itemSelect.setTextColor(QtGui.QColor(self.btPlotItems[mac][3]))
            self.btPlotItems[mac][2] = itemSelect
            if self.ui.selectBeaconList:
                self.ui.selectBeaconList.addItem(itemSelect)

def main():
    # data collect message queue
    dcQueue = Queue.Queue()

    # bluetooth thread
    btQueue = Queue.Queue()

    # define the bluetooth thread
    btThread = BluetoothThread("BluetoothThread", dcQueue, btQueue)
    btThread.setDaemon(True)
    btThread.start()

    app = btLivePlotGui(btQueue, dcQueue)
    app.run()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()
