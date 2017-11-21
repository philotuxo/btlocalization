import sys
sys.path.append('../')
from lib.histograms import *
from multiprocessing import Queue
from multiprocessing import Process
import threading

class FileThread (threading.Thread):
    def __init__(self, name, fileName, wQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.fid = open(fileName, "a")
        self.wQueue = wQueue

    def save(self,message):
        self.fid.write(message)
        self.fid.flush()

    def run(self):
        while True:
            to_be_logged = self.wQueue.get()
            if to_be_logged == "QUIT":
                break
            self.save(to_be_logged)

        self.fid.close()

def workerFunction(pQueue, wQueue, dataHist, beacons):
    # arrange the base set
    base_set = []
    for p in dataHist.keys():
        base_set.append([p[0], p[1]])

    while True:
        if pQueue.qsize() > 0:
            data = pQueue.get()
            if data == "QUIT":
                print("Ending Process")
                break

            i = data[0]
            j = data[1]
            point = data[2]

            closestPoints = find_closest_points(point,
                                            dataHist.keys(),
                                            radius=15.0,
                                            numMax=8)

            print j, i, len(closestPoints)


            weights = []
            for p in closestPoints:
                weights.append(np.exp(-point_euclid(point, p)))

            for beacon in beacons.keys():
                hists = []
                for p in closestPoints:
                    hists.append(dataHist[p][beacon])

                hist = hist_multiple_convex_combination(hists, weights)

                wQueue.put(str(list(point)) + delimiter  +\
                        str(j) + delimiter + \
                        str(i) + delimiter + \
                        str(beacon) + delimiter + \
                        str(list(hist)) + "\n")


if len(sys.argv) > 2:
    fileName = sys.argv[1]
    gridFile = sys.argv[2]
else:
    print "Not enough parameters."
    print "Usage: gridder <histFile> <gridFile>"
    sys.exit()

dataHist, bins, beacons, dataColors = parse_hst_file(fileName)

numProcess = 32

limits = [[0.0, 0.0],[ 6.364366515837104,5.301244343891402]]
sizeGrid = .1
delimiter = "::"

wQueue = Queue()
fThread = FileThread("FileThread", gridFile, wQueue)
fThread.start()

# divide the world into grids
widthGrid =  int(np.ceil(
        limits[1][0]/sizeGrid)) + 1
heightGrid = int(np.ceil(
        limits[1][1]/sizeGrid)) + 1

hist = np.zeros(rssi_end - rssi_start)
header = str(limits) + delimiter + str(sizeGrid) + "\n"
wQueue.put(header)

# create and start processes
processes = []
pQueue = Queue()
for i in range(numProcess):
    p = Process(target=workerFunction, args=(pQueue, wQueue, dataHist, beacons))
    processes.append(p)

for p in processes:
    p.start()

# generate cellVisuals
for j in range(heightGrid):
    for i in range(widthGrid):
        point = (round(limits[0][0] + i
                       *sizeGrid,2),
                 round(limits[0][1] + j
                       *sizeGrid,2) )
        # cellsInv[point] = i + j * widthGrid
        # cells.append({})

        pQueue.put([i,j,point])

# ending processes
for p in range(numProcess):
    pQueue.put("QUIT")

for p in processes:
    p.join()

wQueue.put("QUIT")
fThread.join()
