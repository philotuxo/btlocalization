import threading
import random
import time

class SamplingThread(threading.Thread):
    def __init__(self, threadIndex, inQueue):
        threading.Thread.__init__(self)
        self.inQueue = inQueue
        self.name = "SamplingThread-" + str(threadIndex)
        self.cumulative = None
        self.particles = None
        self.particlesHat = None
        self.bestIndexes = None
        self.bestWeights = None

    def randgen(self):
        pass

    def run(self):
        print self.name + ": Starting."
        while True:
            if self.inQueue.qsize() > 0:
                message = self.inQueue.get()
                if type(message) == int:
                    # this must be an index (integer)
                    index = self.sampleOneFromCumulative(
                            self.cumulative, self.bestIndexes)
                    self.particles[message] = self.particlesHat[index]
                else:
                    if message[0] == "QUIT":
                        print self.name + ": Message Received: " + str(message)
                        print self.name + ": Ending."
                        break
                    if message[0] == 'C':
                        self.cumulative = message[1]
                        # message[1] is the cumulative sum pointer

                    if message[0] == 'P':
                        # Particles
                        self.particles = message[1]

                    if message[0] == 'H':
                        # Particleshat
                        self.particlesHat = message[1]

                    if message[0] == 'I':
                        # indexes
                        self.bestIndexes = message[1]

                    if message[0] == 'W':
                        # Weights
                        self.bestWeights = message[1]

                # time.sleep(0.00001)

    def sampleOneFromCumulative(self, cumulative, indexes):
        rnd = random.uniform(0, 1)
        for i in range(len(cumulative)):
            if rnd <= cumulative[i]:
                ret = indexes[i]
                break

        return ret