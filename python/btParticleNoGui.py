import sys, os, time
from lib.simulationThread import SimulationFileThread
import Queue
from lib.histograms import *
from multiprocessing import Queue as mQueue
from multiprocessing import Process

def processFunction(name, pQueue, doneQueue):
    t = 0
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

def loadParameters(parFile):
    try:
        with open(parFile, 'r') as f:
            tempParams = json.load(f)
            params = {}
            params["limits"] = ( (tempParams["limits"][0],
                                      tempParams["limits"][1]),
                                     (tempParams["limits"][2],
                                      tempParams["limits"][3]))
            print("Parameters loaded: " + parFile)
            return params
    except:
        print("Incompatible File: " + parFile)
        return None

def readConfigFile(configFile):
    try:
        with open(configFile, 'r') as f:
            config = json.load(f)
            print "Config file loaded: " + configFile
            return config
    except:
        print "Problem with the config File: " + configFile
        return None


class btParticleNoGui():
    def __init__(self,
                 fQueue,
                 bQueue,
                 outQueue,
                 pQueues,
                 doneQueue,
                 cells,
                 sizeGrid,
                 widthGrid,
                 heightGrid,
                 bins,
                 limits,
                 numProcess = 4,
                 sizeParticles = 4096,
                 sizeBestWeights = 4096,
                 burnInCount = 32,
                 transitionType = 1, # 0:diffusion, 1:odometry, 2:accelerometer
                 errFile = None):

        self.bins = bins
        self.cells = cells
        self.sizeGrid = sizeGrid
        self.widthGrid = widthGrid
        self.heightGrid = heightGrid
        self.limits = limits

        self.dataHist = {}
        self.beacons = None

        # particles
        self.burnInCount = burnInCount
        self.numProcess = numProcess
        self.sizeParticles = sizeParticles
        self.sizeBestWeights = sizeBestWeights
        self.transitionType = transitionType
        self.pf_likelihood = self.pf_likelihood_grids
        if errFile:
            self.errFile = errFile
        else:
            self.errFile = "someRun" + str(self.sizeParticles) + ".err"

        self.particles = None
        self.particlesHat = None
        self.particleWeights = None
        self.particleWeightedMean = None

        # process messaging
        self.pQueues = pQueues
        self.doneQueue = doneQueue

        # thread messaging
        self.fQueue = fQueue
        self.bQueue = bQueue
        self.inQueue = None
        self.outQueue = outQueue
        self.obsFile = None

        # for fps
        self.lastDataTime = []


    def set_input_items(self, obsFile):
        if len(obsFile) > 1:

            if (obsFile[-3:] == "csv"):
                # select file Queue
                self.changeQueue("f")
                self.inQueue.put(("SFILE", obsFile))

            if (obsFile[-3:] == "trk"):
                # select file Queue
                self.changeQueue("f")
                self.inQueue.put(("TFILE", obsFile))

        else:
            # bluetooth thread
            self.changeQueue("b")

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

    def readData(self, dataFile):
        self.dataFile = dataFile

        # progress dialog patch
        self.dataHist, self.bins, self.beacons, self.macColors = \
            parse_hst_file(self.dataFile)


        print "Histograms loaded: " + self.dataFile

    def runParticleFilter(self):
        self.error = 0
        self.count = 0
        self.burnin = False

        # create the sample base
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
        # send the start signal
        if self.inQueue:
            self.inQueue.put(( "START", None ))

        while True:
            retVal = self.pf_single_step()
            if retVal == "EOF":
                break

        if self.inQueue:
            self.inQueue.put(( "END", None ))


    def pf_single_step(self):
        # get the new data from the queue
        if self.outQueue.qsize() > 0:
            # get new observation
            message = self.outQueue.get()
            if self.count == self.burnInCount:
                self.burnin = True
                print "Burn-in period ended"
                self.error = 0
            if message == "EOF":
                if self.burnin:
                    aveErr = self.error / (self.count - self.burnInCount)
                    print "Average Error = " + str(aveErr)
                    print "with " + str(self.count) + " data points."
                    print "with burn-in at " + str(self.burnInCount)
                else:
                    aveErr = self.error / (self.count)
                    print "Average Error = " + str(aveErr)
                    print "with " + str(self.count) + " data points."

                f = open(self.errFile, 'a+')
                f.write(str(aveErr) + "\n")
                return "EOF"

            point = None
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

            # inifialize if the particles are empty
            # evaluate for the weights
            self.t = time.time()
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
            # print "IS:", time.time() - self.t

            self.t = time.time()
            self.pf_selectParticlesPar()
            # print "SP:", time.time() - self.t

            err = point_euclid((point[0], point[1]), self.particleWeightedMean)
            self.error += err
            self.count += 1
            print "ER:", self.count, err

    def pf_initialize(self):
        # N tane particle at
        if self.transitionType == 0:
            for i in range(self.sizeParticles):
                point = sampleRandomPoint2dUniform(self.limits)
                self.particles[i] = [point]

        if self.transitionType == 1:
            for i in range(self.sizeParticles):
                orient = random.random() * math.pi
                point = sampleRandomPoint2dUniform(self.limits)
                self.particles[i] = [point, orient]

        if self.transitionType == 2:
            for i in range(self.sizeParticles):
                vel = (random.gammavariate(10,.1), random.gammavariate(10,.1))
                acc = (random.gammavariate(10,.01), random.gammavariate(10,.01))
                point = sampleRandomPoint2dUniform(self.limits)
                self.particles[i] = [point, vel, acc]

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
        if point[0] < self.limits[0][0]:
            return False
        if point[1] < self.limits[0][1]:
            return False
        if point[0] > self.limits[1][0]:
            return False
        if point[1] > self.limits[1][1]:
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
        for i in range(self.numProcess):
            # refresh
            self.pQueues[i].put(('r'))
            # send cumulative
            self.pQueues[i].put(('c', cumulative))
            # send bestIndexes
            self.pQueues[i].put(('b', self.bestIndexes))

        # request selection
        for i in range(self.numProcess):
            self.pQueues[i].put(('s', self.sizeParticles/self.numProcess))

        # retrieve selected indexes
        c = 0
        for i in range(self.numProcess):
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

def main():

    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    else:
        configFile = None
        print "ParticleFilter: Not enough parameters."
        sys.exit()

    config = readConfigFile(configFile)
    params = loadParameters(config['par'])
    histFile = config['hst']
    gridFile = config['grd']
    errFile = config['err']
    numProcess = config['prc']
    transitionType = config['trn']
    sizePart = config['szP']
    sizeBest = config['szB']
    burnIn = config['brn']
    trkFile = config['trk']

    # read data and config files here
    pQueues = []
    doneQueue = mQueue()
    for p in range(numProcess):
        q = mQueue()
        pQueues.append(q)

    bQueue = Queue.Queue()
    fQueue = Queue.Queue()
    outQueue = Queue.Queue()
    sThread = SimulationFileThread("FileThread", fQueue, outQueue)

    dataHist, bins, beacons, macColors = parse_hst_file(histFile)
    cells, cellsInv, widthGrid, heightGrid, sizeGrid = read_grids(
            gridFile, delimiter= "::")

    main = btParticleNoGui(fQueue,
                           bQueue,
                           outQueue,
                           pQueues,
                           doneQueue,
                           cells,
                           sizeGrid,
                           widthGrid,
                           heightGrid,
                           bins,
                           params['limits'],
                           errFile= errFile,
                           transitionType = transitionType,
                           sizeParticles= sizePart,
                           sizeBestWeights= sizeBest,
                           burnInCount= burnIn,
                           numProcess = numProcess
)
    main.set_input_items(trkFile)

    # define processes
    processes = []
    for i in range(numProcess):
        p = Process(target=processFunction, args=(str(i), pQueues[i], doneQueue))
        processes.append(p)


    sThread.start()
    # start processes
    for p in processes:
        p.start()

    #start sampThreads
    main.runParticleFilter()

    # end the threads gracefully
    for p in range(numProcess):
        pQueues[p].put("QUIT")
    bQueue.put(["QUIT", None] )
    fQueue.put(["QUIT", None] )

    for p in processes:
        p.join()

    sThread.join()

if __name__ == '__main__':
    main()

