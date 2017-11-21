from PyQt4 import QtCore
from PyQt4 import QtGui
from lib.histograms import *
from lib.histogram_visuals import *
from common import *

class ProbabilityCell(QtGui.QGraphicsRectItem):
    def __init__(self, x, y, prob, radius = 22):
        offset = 0
        QtGui.QGraphicsRectItem.__init__(
                self, x - radius,
                y - radius,
                2*radius,2*radius)

        self.updateProb(prob)
        # true points
        self.truePoint = QtCore.QPoint(x,y)

    def updateProb(self,prob):
        probColor = 255 - int(prob*2048)
        color = QtGui.QColor(probColor, probColor, probColor, 100)
        br = QtGui.QBrush()
        br.setStyle(1)
        br.setColor(color)
        pen = QtGui.QPen(color)

        self.setPen(pen)
        self.setBrush(br)

class Circle(QtGui.QGraphicsEllipseItem):
    def __init__(self, x, y, radius, offset):
        QtGui.QGraphicsEllipseItem.__init__(self, x - offset,
                                            y - offset,
                                            2*radius,2*radius)
        # true points
        self.truePoint = QtCore.QPoint(x,y)

class editableCircle(QtGui.QGraphicsEllipseItem):
    def __init__(self, x, y, radius, offset, btV):
        QtGui.QGraphicsEllipseItem.__init__(self, x - offset,
                                            y - offset,
                                            2*radius, 2*radius)
        # true points, we print the points with offset because of the
        # rectangular manner of the ellipse object
        self.truePoint = QtCore.QPoint(x,y)
        self.btV = btV

    def mousePressEvent(self, event):
        if self.btV.ui.edit.isChecked():
            self.btV.putPointInputBox(self.truePoint)
            self.btV.circleRemove = self

class btImageScene(QtGui.QGraphicsScene):
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


    def setImageSize(self, size):
        self.sizeX = size.width()
        self.sizeY = size.height()

    def mousePressEvent(self, event):
        self.latestPoint = QtCore.QPoint(event.scenePos().x(),
                                         event.scenePos().y())

    def addPoint(self, point, text, color, pencolor = None, radius = 4,
                 editable = False):
        xoffset = 5
        yoffset = 8
        br = QtGui.QBrush()
        br.setStyle(1)
        br.setColor(color)
        brText = QtGui.QBrush()
        brText.setStyle(1)
        brText.setColor(QtGui.QColor(64,64,64))
        if pencolor == None:
            pen = QtGui.QPen(color)
        else:
            pen = pencolor

        if editable:
            newCircle = editableCircle(
                        point.x(),
                        point.y(),
                        radius,
                        radius,
                        self.btV)
        else:
            newCircle = Circle(
                        point.x(),
                        point.y(),
                        radius,
                        radius)

        newCircle.setBrush(br)
        newCircle.setPen(pen)

        # text arrangement for the borders, does not work actually
        if point.x() > radius \
                and point.y() > radius \
                and point.x() < self.sizeX - radius \
                and point.y() < self.sizeY - radius:

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

            # if len(text)
            newText = QtGui.QGraphicsSimpleTextItem(text)
            newText.setPos(
                text_x - 12,
                text_y
            )

            newText.setFont(QtGui.QFont('Mono',6))
            newText.setParentItem(newCircle)

            newText.setBrush(brText)
            self.addItem(newCircle)
        return newCircle


    def clearParameters(self):
        if self.originPoint:
            self.removeItem(self.originPoint)
        for line in self.positiveDirLines:
            if line:
                self.removeItem(line)
        if self.tempCircle:
            self.removeItem(self.tempCircle)
            self.tempCircle = None

        if self.frame[0]:
            for i in range(0,4):
                self.removeItem(self.frame[i])


    def putParameters(self):
        # put graphics
        if self.btV.params["origin"]:
            self.originPoint = self.addPoint(self.btV.params["origin"],"",
                                              QtGui.QColor(0,0,0))
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

        if self.btV.params["limits"]:
            if self.btV.params["origin"] and self.btV.params["parity"] and self.btV.params["direction"]:
                p0 = real2Pix(self.btV.params, self.btV.params["limits"][0])
                p1 = real2Pix(self.btV.params, self.btV.params["limits"][1])
                self.frame[0] = self.addLine(p0.x(),p0.y(),p0.x(),p1.y(),
                                QtGui.QPen(QtGui.QColor(255,0,255)))
                self.frame[1] = self.addLine(p0.x(),p0.y(),p1.x(),p0.y(),
                                QtGui.QPen(QtGui.QColor(255,0,255)))
                self.frame[2] = self.addLine(p0.x(),p1.y(),p1.x(),p1.y(),
                                QtGui.QPen(QtGui.QColor(255,0,255)))
                self.frame[3] = self.addLine(p1.x(),p0.y(),p1.x(),p1.y(),
                                QtGui.QPen(QtGui.QColor(255,0,255)))

    def getArrowHead(self, s, d, headsize = 8):
        dx, dy = s.x() - d.x(), s.y() - d.y()
        norm = math.sqrt(dx**2 + dy**2)
        udx, udy = dx/norm, dy/norm
        ax = udx * math.sqrt(3)/2 - udy * 1/2
        ay = udx * 1/2 + udy * math.sqrt(3)/2
        bx = udx * math.sqrt(3)/2 + udy * 1/2
        by =  - udx * 1/2 + udy * math.sqrt(3)/2

        return (d.x()+headsize*ax, d.y()+headsize *ay), \
               (d.x()+headsize*bx, d.y()+headsize *by)

    def putArrow(self, s, d, rgb = None):
        if rgb:
            pen = QtGui.QPen(QtGui.QColor(rgb2int(rgb)))
        else:
            pen = QtGui.QPen(QtGui.QColor(0,255,0))

        if not s == d:
            # norm 0 olmasin diye koyduk bu if'i
            arrow1, arrow2 = self.getArrowHead(s, d)
            self.addLine(
                s.x(),
                s.y(),
                d.x(),
                d.y(),
                pen
            )

            self.positiveDirLines[1] = self.addLine(
                d.x(),
                d.y(),
                arrow1[0],
                arrow1[1],
                pen
            )

            self.positiveDirLines[2] = self.addLine(
                d.x(),
                d.y(),
                arrow2[0],
                arrow2[1],
                pen
            )

