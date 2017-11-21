from PyQt4 import QtGui
import sys, os
from lib.btTrack_ui import Ui_btTrack
from lib.histogram_visuals import *
from lib.btQtCore import *

class TrackImageScene(btImageScene):
    def __init__(self, btViewerGui):
        QtGui.QGraphicsScene.__init__(self)
        self.circleRadius = 3
        self.latestPoint = None
        self.originPoint = None
        self.positiveDirLines = [ None, None, None ]
        self.tempCircle = None
        self.btV = btViewerGui
        self.limits = [ None, None ]
        self.frame = [ None, None, None, None ]
        self.arrowLength = 7

    def putTempCircle(self):
        # tempCircle to delete when needed
        if self.latestPoint:
            self.tempCircle = self.addPoint(self.latestPoint,"",color =
            QtGui.QColor(255,0,0))

    def mousePressEvent(self, event):
        self.latestPoint = QtCore.QPoint(event.scenePos().x(),
                                         event.scenePos().y())

        realPt = pix2Real(self.btV.params, self.latestPoint)

        self.btV.addTrackPoint(point=realPt)
        self.btV.updateImage()

class btViewerGui(QtGui.QMainWindow):
    def __init__(self, configFile = None):
        self.qt_app = QtGui.QApplication(sys.argv)
        QtGui.QWidget.__init__(self, None)

        # create the main ui
        self.ui = Ui_btTrack()
        self.ui.setupUi(self)
        self.imageScene = TrackImageScene(self)

        self.colorlines = colorlines
        self.colorlines.reverse()

        self.macColors = {}
        self.dataHist = {}
        self.beacons = None

        # imageButton
        self.imageFile = None

        # calibration
        self.params = {}
        self.params["parity"] = None
        self.params["origin"] = None
        self.params["direction"] = None
        self.params["limits"] = None

        # synthetic data generation
        self.track = []
        self.playAccelPairs = []
        self.playOdomPairs = []
        self.noisyTrack = []

        # trajectory parameters
        self.turnoffset = math.pi/8
        self.sizeRandomPoints = 50
        self.distAlpha = 20
        self.distBeta = .01
        self.timeAlpha = 60
        self.timeBeta = .01
        self.distThresh = .75
        self.varTheta = .1

        # beacon probability
        self.beaconsProbs = None

        # timers
        self.pTimer = QtCore.QTimer()

        # config file
        if configFile:
            self.configFile = configFile
            self.configFileCheck()

        self.ui.saveTrackButton.clicked.connect(self.saveTrackToFile)
        self.ui.saveNoiseTrackButton.clicked.connect(self.saveNoisyTrackToFile)
        self.ui.loadTrackButton.clicked.connect(self.loadTrackFromFile)
        self.ui.clearTrackButton.clicked.connect(self.clearTrack)
        self.ui.randomizeTrackButton.clicked.connect(self.generateTrajectory)
        self.ui.noiseButton.clicked.connect(self.addNoise)
        self.ui.simulateAButton.clicked.connect(self.simulateAcceleration)
        self.ui.simulateHButton.clicked.connect(self.simulateHeading)
        # self.ui.noiseAcceleration.clicked.connect(self.addNoiseAccel)

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

    def resetImagePressed(self):
        self.imageFile = None
        self.updateImage()

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

        self.beaconsProbs = [1.0 * len(self.beacons) ] * len(self.beacons)

        print "Histograms loaded: " + self.dataFile

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
        self.frame = self.setOpacity(0.2)
        self.imageScene.clearParameters()
        self.imageScene.clear()
        self.imageScene.addPixmap(QtGui.QPixmap.fromImage(self.frame))
        self.imageScene.setImageSize(self.frame.size())
        self.imageScene.update()
        self.ui.imageView.setScene(self.imageScene)
        self.putBeacons()
        self.putPoints()
        self.putLines()
        if self.imageFile:
            # self.imageScene.clearParameters()
            self.imageScene.putParameters()
            # self.imageScene.putTempCircle()

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
        for pts in self.track:
            color = QtGui.QColor(255,255,255)
            self.imageScene.addPoint(
                    real2Pix(self.params, (pts[1][0],pts[1][1])) ,"", color,
                    pencolor=QtGui.QColor(0,0,0), radius= 3 )


    def addTrackPoint(self, point = None):
        if len(self.track) == 0:
            # this will be the first point
            # put the time stamp as 0.0
            timeStamp = 0.0

            if not point:
                # generate a new point on the map.
                point = sampleRandomPoint2dUniform(self.params["limits"])

            # generate an initial orientation
            theta = random.random()* math.pi

            # combine pose
            pose = [point[0], point[1], theta]

            mac, rssi = self.generateBeaconData(point)

            self.track.append(
                    [timeStamp,
                     pose, # pose in the global frame
                     None, # velocity in forward direction
                     0, # yaw in the global frame
                     (0,0), # velocity in x,y
                     None, # yaw rate
                     None, # acceleration in x,y
                     mac,  # beacon
                     rssi  # rssi
                     ])
        else:

            if len(self.track) >= 1:

                timeDelta = round(random.gammavariate(
                        self.timeAlpha, self.timeBeta),2)
                timeStamp = round(self.track[-1][0] + timeDelta,2)

                if point:
                    # get old point
                    oldpoint = (
                        self.track[-1][1][0], self.track[-1][1][1])

                    thetaPrev = self.track[-1][1][2]


                    # get the previous distance
                    dist = math.sqrt(
                            (point[0] - oldpoint[0]) **2 +
                            (point[1] - oldpoint[1]) **2)

                    theta = math.atan2(point[1] - oldpoint[1],
                                       point[0] - oldpoint[0])

                    thetaDelta = theta - thetaPrev

                else:

                    # get the point
                    pointPrev = self.track[-1][1][0:2]

                    # get the previous deltas
                    thetaPrev = self.track[-1][1][2]
                    # sample a delta theta
                    thetaDelta = self.randomDTheta(pointPrev,thetaPrev)
                    # sample a dist
                    dist = self.randomDist()

                    # new theta
                    theta = (thetaPrev + thetaDelta) % (2*math.pi)

                    # add on to generate the new point
                    point = (
                        self.track[-1][1][0] + dist * math.cos(theta),
                        self.track[-1][1][1] + dist * math.sin(theta)
                    )

                pose = [point[0],point[1],theta]

                # update velocity and acceleration
                # find the velocity in two directions at previous time stamp
                xVeloc = (pose[0] - self.track[-1][1][0])/timeDelta
                yVeloc = (pose[1] - self.track[-1][1][1])/timeDelta

                # acceleration update
                xAccel = (xVeloc - self.track[-1][4][0]) / \
                         timeDelta
                yAccel = (yVeloc - self.track[-1][4][1]) / \
                         timeDelta

                yawRate = (thetaDelta - self.track[-1][3]) / timeDelta

                mac, rssi = self.generateBeaconData(point)
                # write the vector
                self.track.append(
                        [timeStamp,
                         pose, # pose in the global frame
                         dist, # velocity in forward direction
                         thetaDelta, # yaw in the global frame
                         (xVeloc, yVeloc), # velocity in x,y
                         yawRate, # yaw rate
                         (xAccel, yAccel), # acceleration in x,y
                         mac,  # beacon
                         rssi  # rssi
                         ])


    def putLines(self):
        if len(self.track) == 0:
            return
        if not len(self.track) > 1:
            return

        for i in range(1,len(self.track)):
            p1 = real2Pix(self.params,
                          (self.track[i-1][1][0], self.track[i-1][1][1]))
            p2 = real2Pix(self.params,
                          (self.track[i][1][0], self.track[i][1][1]))

            self.imageScene.addArrow(p1,p2,(255,0,0))

        if len(self.playOdomPairs) > 0:
            for pair in self.playOdomPairs:
                p1 = real2Pix(self.params, pair[0])
                p2 = real2Pix(self.params, pair[1])

                self.imageScene.addArrow(p1,p2,(0,0,255))

        if len(self.playAccelPairs) > 0:
            for pair in self.playAccelPairs:
                p1 = real2Pix(self.params, pair[0])
                p2 = real2Pix(self.params, pair[1])

                self.imageScene.addArrow(p1,p2,(0,255,0))

    def generateBeaconData(self, point):
        # find the closest fingerprint
        closest = find_closest_points(point,
                                      self.dataHist.keys(),
                                      radius=5.0,
                                      numMax=1)


        # select randomly a beacon from the available beacons
        # kullanildikca olasiligin azalmasi gerekiyor
        b = randgen(self.beaconsProbs,1)
        self.beaconsProbs[b[0]] = self.beaconsProbs[b[0]]/2.0

        # normalize
        s = sum(self.beaconsProbs)
        for i in range(len(self.beaconsProbs)):
            self.beaconsProbs[i] = self.beaconsProbs[i]/s

        rssi = randgen(
                self.dataHist[closest[0]][self.beacons.keys()[b[0]]],
                1, self.bins[:-1])
        return self.beacons.keys()[b[0]], rssi[0]



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

    def saveTrackToFile(self):
        trackFile = QtGui.QFileDialog.getSaveFileName(self,
                                                        'Save file',
                                                        '../data/untitled.trk',
                                                        'Tracking Data (*.trk)')
        with open(trackFile, 'w') as f:
            print "Writing to file: "  + trackFile
            # generate a tempFile

            for pts in self.track:
                f.write(str(pts) + '\n')
            print "Track Points saved to " + \
                  os.path.basename(str(trackFile)) + "."

    def saveNoisyTrackToFile(self):
        trackFile = QtGui.QFileDialog.getSaveFileName(self,
                                                        'Save file',
                                                        '../data/untitled.trk',
                                                        'Tracking Data (*.trk)')
        with open(trackFile, 'w') as f:
            print "Writing to file: "  + trackFile
            # generate a tempFile

            for i in range(len(self.noisyTrack)):
                line = self.noisyTrack[i]

                line[1] = self.track[i][1] # put the original point
                f.write(str(line) + '\n')
            print "Track Points saved to " + \
                  os.path.basename(str(trackFile)) + "."


    def loadTrackFromFile(self):
        tFile = QtGui.QFileDialog.getOpenFileName(self,
                                                  'Open file',
                                                  '../data/',
                                                  'Track Data (*.trk)')
        try:
            with open(tFile, 'r') as f:
                self.track = []
                for line in f:
                    each = literal_eval(line.strip())
                    self.track.append(each)


                print "Data file loaded "+ tFile
                self.updateImage()
        except:
            print "Incompatible data file: " + tFile


    def clearTrack(self):
        self.track = []
        self.playAccelPairs = []
        self.playOdomPairs = []
        self.noisyTrack = []
        self.updateImage()

    def randomDTheta(self, point, prevTheta, distThresh = None):
        if not distThresh:
            distThresh = self.distThresh
        prevTheta = prevTheta % (2 * math.pi)
        theta = prevTheta

        if self.params["limits"][1][0] - point[0] < distThresh:
            if theta < math.pi:
                theta += self.turnoffset
            if theta > math.pi:
                theta -= self.turnoffset

        elif point[0] - self.params["limits"][0][0] < distThresh:
            if theta < math.pi:
                theta -= self.turnoffset
            if theta > math.pi:
                theta += self.turnoffset

        elif self.params["limits"][1][1] - point[1] < distThresh:
            if theta > math.pi/2 and theta < 3* math.pi/2:
                theta += self.turnoffset
            if theta < math.pi/2 or theta > 3*math.pi/2:
                theta -= self.turnoffset

        elif point[1] - self.params["limits"][0][1] < distThresh:
            if theta > math.pi/2 and theta < 3* math.pi/2:
                theta -= self.turnoffset
            if theta < math.pi/2 or theta > 3*math.pi/2:
                theta += self.turnoffset

        else:
            # get a new orientation via normal distribution
            theta = random.normalvariate(theta, self.varTheta)

        diff = theta - prevTheta
        if abs(diff) > math.pi:
            return math.pi - diff
        else:
            return diff

    def randomDist(self):
        # get a random distance around .3 meters
        dist = random.gammavariate(self.distAlpha, self.distBeta)
        return dist

    def generateTrajectory(self):
        # get a random point in the map with random orientation
        for i in range(self.sizeRandomPoints):
            self.addTrackPoint()

        self.updateImage()

    def playTrajectoryHeading(self):
        self.playOdomPairs = []
        if len(self.noisyTrack) == 0:
            self.noisyTrack = list(self.track)
        for i in range(0,len(self.noisyTrack)):
            if i == 0:
                # get the start point
                point0 = (self.noisyTrack[i][1][0], self.noisyTrack[i][1][1])
                theta = self.noisyTrack[i][1][2]
                # find the next point
            else:
                dist = self.noisyTrack[i][2]
                theta = self.noisyTrack[i][3] + theta
                x = dist * math.cos(theta)
                y = dist * math.sin(theta)

                point1 = (point0[0] + x, point0[1] + y)
                self.playOdomPairs.append((point0, point1))

                point0 = point1

        self.updateImage()

    def playTrajectoryAccel(self):
        self.playAccelPairs = []
        if len(self.noisyTrack) == 0:
            self.noisyTrack = list(self.track)
        for i in range(0,len(self.noisyTrack)):
            if i == 0:
                # get the initial state point
                point0 = (self.noisyTrack[i][1][0], self.noisyTrack[i][1][1])
                vel_x = self.noisyTrack[i][4][0]
                vel_y = self.noisyTrack[i][4][1]

            else:

                timeDelta = self.noisyTrack[i][0] - self.noisyTrack[i-1][0]
                acc_x = self.noisyTrack[i][6][0]
                acc_y = self.noisyTrack[i][6][1]

                vel_x = vel_x + timeDelta * acc_x
                vel_y = vel_y + timeDelta * acc_y


                point1 = (point0[0] + vel_x * timeDelta,
                          point0[1] + vel_y * timeDelta)

                self.playAccelPairs.append((point0, point1))

                point0 = point1

        self.updateImage()

    def simulateHeading(self):
        self.playAccelPairs = []
        self.playOdomPairs = []
        self.noisyTrack = list(self.track)
        self.playTrajectoryHeading()

    def simulateAcceleration(self):
        self.playAccelPairs = []
        self.playOdomPairs = []
        self.noisyTrack = list(self.track)
        self.playTrajectoryAccel()


    def addNoise(self):

        self.noisyTrack = []
        for i in range(len(self.track)):
            if i == 0:
                line = [ self.track[i][0],
                         self.track[i][1],
                         0,
                         self.track[i][3], # yaw not needed but initial
                         self.track[i][4], # velocity not needed, but initial
                         0,
                         (0,0),
                         self.track[i][7],
                         self.track[i][8]
                         ]
            else:
                line = [ self.track[i][0],
                         None, # entry 1 is written when saving
                         None,
                         None,
                         None,
                         None,
                         None,
                         self.track[i][7],
                         self.track[i][8]
                         ]

            if i >= 1:
                acc_x = random.normalvariate(self.track[i][6][0],.02)
                acc_y = random.normalvariate(self.track[i][6][1],.02)
                yawrate = random.normalvariate(self.track[i][5],.01)

                line[6] = (acc_x, acc_y)
                line[5] = yawrate

                dist = random.normalvariate(self.track[i][2],.05)
                deltaTheta = random.normalvariate(self.track[i][3],.05)

                line[2] = dist
                line[3] = deltaTheta

            self.noisyTrack.append(line)

        self.playTrajectoryAccel()
        self.playTrajectoryHeading()

def main():

    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    else:
        sys.exit("Config file required!")

    app = btViewerGui(configFile)
    app.run()

    # end the threads gracefully

if __name__ == '__main__':
    main()

