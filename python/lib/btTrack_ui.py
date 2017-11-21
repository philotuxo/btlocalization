# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/btTrack.ui'
#
# Created: Sun Mar  6 16:20:33 2016
#      by: PyQt4 UI code generator 4.11.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_btTrack(object):
    def setupUi(self, btTrack):
        btTrack.setObjectName(_fromUtf8("btTrack"))
        btTrack.resize(740, 520)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(btTrack.sizePolicy().hasHeightForWidth())
        btTrack.setSizePolicy(sizePolicy)
        btTrack.setMaximumSize(QtCore.QSize(1200, 520))
        self.imageView = QtGui.QGraphicsView(btTrack)
        self.imageView.setGeometry(QtCore.QRect(10, 10, 721, 480))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.imageView.sizePolicy().hasHeightForWidth())
        self.imageView.setSizePolicy(sizePolicy)
        self.imageView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.imageView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.imageView.setObjectName(_fromUtf8("imageView"))
        self.saveTrackButton = QtGui.QPushButton(btTrack)
        self.saveTrackButton.setGeometry(QtCore.QRect(200, 490, 71, 23))
        font = QtGui.QFont()
        font.setPointSize(7)
        self.saveTrackButton.setFont(font)
        self.saveTrackButton.setObjectName(_fromUtf8("saveTrackButton"))
        self.loadTrackButton = QtGui.QPushButton(btTrack)
        self.loadTrackButton.setGeometry(QtCore.QRect(140, 490, 61, 23))
        font = QtGui.QFont()
        font.setPointSize(7)
        self.loadTrackButton.setFont(font)
        self.loadTrackButton.setObjectName(_fromUtf8("loadTrackButton"))
        self.clearTrackButton = QtGui.QPushButton(btTrack)
        self.clearTrackButton.setGeometry(QtCore.QRect(80, 490, 61, 23))
        font = QtGui.QFont()
        font.setPointSize(7)
        self.clearTrackButton.setFont(font)
        self.clearTrackButton.setObjectName(_fromUtf8("clearTrackButton"))
        self.randomizeTrackButton = QtGui.QPushButton(btTrack)
        self.randomizeTrackButton.setGeometry(QtCore.QRect(10, 490, 71, 23))
        font = QtGui.QFont()
        font.setPointSize(7)
        self.randomizeTrackButton.setFont(font)
        self.randomizeTrackButton.setObjectName(_fromUtf8("randomizeTrackButton"))
        self.noiseButton = QtGui.QPushButton(btTrack)
        self.noiseButton.setGeometry(QtCore.QRect(580, 490, 71, 23))
        font = QtGui.QFont()
        font.setPointSize(7)
        self.noiseButton.setFont(font)
        self.noiseButton.setObjectName(_fromUtf8("noiseButton"))
        self.saveNoiseTrackButton = QtGui.QPushButton(btTrack)
        self.saveNoiseTrackButton.setGeometry(QtCore.QRect(660, 490, 71, 23))
        font = QtGui.QFont()
        font.setPointSize(7)
        self.saveNoiseTrackButton.setFont(font)
        self.saveNoiseTrackButton.setObjectName(_fromUtf8("saveNoiseTrackButton"))
        self.label = QtGui.QLabel(btTrack)
        self.label.setGeometry(QtCore.QRect(530, 494, 41, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.simulateHButton = QtGui.QPushButton(btTrack)
        self.simulateHButton.setGeometry(QtCore.QRect(370, 490, 71, 23))
        font = QtGui.QFont()
        font.setPointSize(7)
        self.simulateHButton.setFont(font)
        self.simulateHButton.setObjectName(_fromUtf8("simulateHButton"))
        self.simulateAButton = QtGui.QPushButton(btTrack)
        self.simulateAButton.setGeometry(QtCore.QRect(440, 490, 71, 23))
        font = QtGui.QFont()
        font.setPointSize(7)
        self.simulateAButton.setFont(font)
        self.simulateAButton.setObjectName(_fromUtf8("simulateAButton"))

        self.retranslateUi(btTrack)
        QtCore.QMetaObject.connectSlotsByName(btTrack)

    def retranslateUi(self, btTrack):
        btTrack.setWindowTitle(_translate("btTrack", "Track Logger", None))
        self.saveTrackButton.setText(_translate("btTrack", "Save", None))
        self.loadTrackButton.setText(_translate("btTrack", "Load", None))
        self.clearTrackButton.setText(_translate("btTrack", "Clear", None))
        self.randomizeTrackButton.setText(_translate("btTrack", "Randomize", None))
        self.noiseButton.setText(_translate("btTrack", "Add Noise", None))
        self.saveNoiseTrackButton.setText(_translate("btTrack", "Save Noise", None))
        self.label.setText(_translate("btTrack", "Noise:", None))
        self.simulateHButton.setText(_translate("btTrack", "SimulateH", None))
        self.simulateAButton.setText(_translate("btTrack", "SimulateA", None))

