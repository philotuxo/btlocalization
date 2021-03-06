# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/btParticle.ui'
#
# Created: Wed Mar 30 00:37:04 2016
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

class Ui_btParticle(object):
    def setupUi(self, btParticle):
        btParticle.setObjectName(_fromUtf8("btParticle"))
        btParticle.resize(900, 720)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(btParticle.sizePolicy().hasHeightForWidth())
        btParticle.setSizePolicy(sizePolicy)
        btParticle.setMinimumSize(QtCore.QSize(900, 720))
        btParticle.setMaximumSize(QtCore.QSize(900, 720))
        self.loadImageButton = QtGui.QPushButton(btParticle)
        self.loadImageButton.setGeometry(QtCore.QRect(280, 10, 41, 21))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.loadImageButton.setFont(font)
        self.loadImageButton.setObjectName(_fromUtf8("loadImageButton"))
        self.imageView = QtGui.QGraphicsView(btParticle)
        self.imageView.setGeometry(QtCore.QRect(180, 30, 711, 681))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.imageView.sizePolicy().hasHeightForWidth())
        self.imageView.setSizePolicy(sizePolicy)
        self.imageView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.imageView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.imageView.setObjectName(_fromUtf8("imageView"))
        self.noImageLabel = QtGui.QLabel(btParticle)
        self.noImageLabel.setGeometry(QtCore.QRect(490, 280, 121, 20))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(30, 30, 40))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(20, 19, 18))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush)
        self.noImageLabel.setPalette(palette)
        self.noImageLabel.setObjectName(_fromUtf8("noImageLabel"))
        self.resetImageButton = QtGui.QPushButton(btParticle)
        self.resetImageButton.setGeometry(QtCore.QRect(320, 10, 41, 21))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.resetImageButton.setFont(font)
        self.resetImageButton.setObjectName(_fromUtf8("resetImageButton"))
        self.label = QtGui.QLabel(btParticle)
        self.label.setGeometry(QtCore.QRect(200, 12, 81, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.resetDataButton = QtGui.QPushButton(btParticle)
        self.resetDataButton.setGeometry(QtCore.QRect(70, 10, 41, 21))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.resetDataButton.setFont(font)
        self.resetDataButton.setObjectName(_fromUtf8("resetDataButton"))
        self.beaconsAvailable = QtGui.QListWidget(btParticle)
        self.beaconsAvailable.setGeometry(QtCore.QRect(10, 280, 161, 121))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Andale Mono"))
        self.beaconsAvailable.setFont(font)
        self.beaconsAvailable.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.beaconsAvailable.setObjectName(_fromUtf8("beaconsAvailable"))
        self.pointsAvailable = QtGui.QListWidget(btParticle)
        self.pointsAvailable.setGeometry(QtCore.QRect(10, 60, 161, 211))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Andale Mono"))
        font.setBold(False)
        font.setItalic(False)
        font.setUnderline(False)
        font.setWeight(50)
        self.pointsAvailable.setFont(font)
        self.pointsAvailable.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.pointsAvailable.setObjectName(_fromUtf8("pointsAvailable"))
        self.readDataButton = QtGui.QPushButton(btParticle)
        self.readDataButton.setGeometry(QtCore.QRect(10, 10, 61, 21))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.readDataButton.setFont(font)
        self.readDataButton.setObjectName(_fromUtf8("readDataButton"))
        self.loadParametersButton = QtGui.QPushButton(btParticle)
        self.loadParametersButton.setGeometry(QtCore.QRect(460, 10, 41, 21))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.loadParametersButton.setFont(font)
        self.loadParametersButton.setObjectName(_fromUtf8("loadParametersButton"))
        self.label_3 = QtGui.QLabel(btParticle)
        self.label_3.setGeometry(QtCore.QRect(380, 12, 81, 16))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.dataFile = QtGui.QLabel(btParticle)
        self.dataFile.setGeometry(QtCore.QRect(10, 40, 161, 16))
        self.dataFile.setObjectName(_fromUtf8("dataFile"))
        self.buttonStart = QtGui.QPushButton(btParticle)
        self.buttonStart.setGeometry(QtCore.QRect(770, 10, 61, 21))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.buttonStart.setFont(font)
        self.buttonStart.setObjectName(_fromUtf8("buttonStart"))
        self.buttonStop = QtGui.QPushButton(btParticle)
        self.buttonStop.setGeometry(QtCore.QRect(830, 10, 61, 21))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.buttonStop.setFont(font)
        self.buttonStop.setObjectName(_fromUtf8("buttonStop"))
        self.collectDataShow = QtGui.QListWidget(btParticle)
        self.collectDataShow.setGeometry(QtCore.QRect(10, 440, 161, 141))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Andale Mono"))
        font.setPointSize(6)
        self.collectDataShow.setFont(font)
        self.collectDataShow.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.collectDataShow.setObjectName(_fromUtf8("collectDataShow"))
        self.inputComboBox = QtGui.QComboBox(btParticle)
        self.inputComboBox.setGeometry(QtCore.QRect(581, 10, 191, 21))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Sans Serif"))
        font.setPointSize(8)
        self.inputComboBox.setFont(font)
        self.inputComboBox.setObjectName(_fromUtf8("inputComboBox"))
        self.dps = QtGui.QLabel(btParticle)
        self.dps.setGeometry(QtCore.QRect(10, 420, 161, 16))
        self.dps.setObjectName(_fromUtf8("dps"))

        self.retranslateUi(btParticle)
        QtCore.QMetaObject.connectSlotsByName(btParticle)

    def retranslateUi(self, btParticle):
        btParticle.setWindowTitle(_translate("btParticle", "Particle Filter", None))
        self.loadImageButton.setText(_translate("btParticle", "Load", None))
        self.noImageLabel.setText(_translate("btParticle", "No Image Loaded", None))
        self.resetImageButton.setText(_translate("btParticle", "Clear", None))
        self.label.setText(_translate("btParticle", "Map Image:", None))
        self.resetDataButton.setText(_translate("btParticle", "Reset", None))
        self.readDataButton.setText(_translate("btParticle", "Add Files", None))
        self.loadParametersButton.setText(_translate("btParticle", "Load", None))
        self.label_3.setText(_translate("btParticle", "Parameters:", None))
        self.dataFile.setText(_translate("btParticle", "File:", None))
        self.buttonStart.setText(_translate("btParticle", "Start", None))
        self.buttonStop.setText(_translate("btParticle", "Stop", None))
        self.dps.setText(_translate("btParticle", "DPS:", None))

