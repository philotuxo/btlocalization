__author__ = 'serhan'

import numpy as np
import random
import math
from colorlines import colorlines
from itertools import combinations
from test_data import *
import time
import json
from ast import literal_eval
from operator import add
import sys

rssi_start = -125
rssi_end = -55
oneday = 60*60*24

def data_generate_rssi(N,params = None):
    if not params:
        params = (np.random.poisson(30)-120,np.random.uniform(.5, 4))
    data = np.random.normal(params[0],params[1],N)
    b = np.empty((len(data),),dtype='int')
    data_int = np.round(data)
    return data_int

def data_generate_rssi_two_peaks(N):
    params = (np.random.poisson(30)-120,np.random.uniform(.5,4),
                np.random.poisson(30)-120,np.random.uniform(.5,4))

    data0 = np.random.normal(params[0],params[1],int(N/2))
    data1 = np.random.normal(params[2],params[3],N-int(N/2))

    return np.append(data0, data1)

def hist_normalize(hist):
    data = np.array(hist,np.dtype(Decimal))
    return data/float(np.sum(data))

def hist_normalize_with(hist, num):
    data = np.array(hist,np.dtype(Decimal))
    return data/float(num)


def hist_from_data(data, limits = [rssi_start, rssi_end]):
    # generate histogram from the given data
    hist, bins = np.histogram(
        data, limits[1]-limits[0] , range = (limits[0], limits[1]))
    return hist, bins

def hist_convex_combination(hist0, hist1, alpha):
    # compute the comvex combination of two vectors
    assert(validate(hist0,hist1))
    hist = np.zeros(len(hist0))
    for i in range(0,len(hist0)):
        hist[i] = hist0[i] * alpha + hist1[i] * (1-alpha)
    return hist

def hist_multiple_convex_combination(hists, alpha):
    # compute the comvex combination of multiple vectors
    # assert(validate(hist0,hist1))
    alpha = hist_normalize(alpha)
    hist = np.zeros(len(hists[0]))
    for i in range(0,len(hists[0])):
        for j in range(0,len(hists)):
            hist[i] += hists[j][i] * alpha[j]
    return hist


def hist_merge(hists, weights, type = 'prop'):
    hist = np.zeros(len(hists[0]))
    if type == 'inv':
        weights = 1 - weights
        weights = weights/float(sum(weights))
    if not sum(weights) == 1:
        weights = weights/float(sum(weights))


    # print type(hists)
    for i in range(0,len(hists)):
        for j in range(0,len(hists[i])):
            hist[j] += hists[i][j] * weights[i]
    return hist


def hist_wasserstein_interpolation(mapping, t, beta,
                                   limits=(rssi_start, rssi_end)):
    # print mapping
    hist = np.zeros(limits[1] - limits[0])

    # print alpha, beta
    for each in mapping.keys():
        # k = each[0] + alpha * (each[1]-each[0])
        # k1 = int(k + (each[0]-k) * (1-beta))
        # k2 = int(k + (each[1]-k) * (1-beta))
        k1 = np.ceil(each[0] + t * beta * (each[1] - each[0]))
        k2 = np.ceil(each[1] + (1-t) * beta * (each[0] - each[1]))
        if k1 < 0 or k1 >= len(hist) or k2 < 0 or k2 >= len(hist):
            continue

        hist[k1] = hist[k1] + abs(1-t)/float(abs(1-t) + abs(t)) * mapping[each]
        hist[k2] = hist[k2] + abs(t)/float(abs(1-t) + abs(t)) * mapping[each]
    return hist

def hist_wasserstein_interpolation_smooth(mapping, t, beta):
    hist = np.zeros(rssi_end - rssi_start)

    for each in mapping.keys():
        i0 = each[0] + t * (each[1]-each[0])
        i1 = each[0] + t * (each[1]-i0)
        i2 = each[0] + t * (each[1]-i1)

        hist[i0] = hist[i0] + (1-t) * mapping[each]
        hist[i1] = hist[i1] + t * (1-t) * mapping[each]
        hist[i2] = hist[i2] + t * t * mapping[each]

    return hist

def hist_jaccard(hist0, hist1):

    assert(validate(hist0,hist1))
    return sum(abs(hist0-hist1))

def validate(hist0, hist1):
    if len(hist0) == len(hist1):
        return True
    else:
        print("Error: Vector lengths not equal")
        return False

def hist_wasserstein(hist0, hist1):
    # calculate the wasserstein metric
    # and generate the mapping between hist0 to hist1
    assert(validate(hist0, hist1))

    x = np.array(hist0,np.dtype(Decimal))
    y = np.array(hist1,np.dtype(Decimal))
    WasserMap = {}
    SIZE = len(x)

    SUM = 0
    i = 0
    j = 0

    while i < SIZE and j < SIZE:
        if x[i] == 0 and not i == SIZE - 1:
            i = i + 1
            continue
        if y[j] == 0 and not j == SIZE - 1:
            j = j + 1
            continue

        if x[i] < y[j]:
            y[j] = y[j] - x[i]
            SUM = SUM + x[i] * abs(i-j)
            WasserMap[(i,j)] = x[i]
            x[i] = 0
            i = i + 1
        else:
            x[i] = x[i] - y[j]
            SUM = SUM + y[j] * abs(i-j)
            WasserMap[(i,j)] = y[j]
            y[j] = 0
            j = j + 1

    return SUM, WasserMap

def hist_wasserstein_distance(hist0, hist1):
    # calculate the wasserstein metric
    # and generate the mapping between hist0 to hist1
    assert(validate(hist0, hist1))

    x = np.array(hist0,np.dtype(Decimal))
    y = np.array(hist1,np.dtype(Decimal))
    SIZE = len(x)

    SUM = 0
    i = 0
    j = 0

    while i < SIZE and j < SIZE:
        if x[i] == 0 and not i == SIZE - 1:
            i = i + 1
            continue
        if y[j] == 0 and not j == SIZE - 1:
            j = j + 1
            continue

        if x[i] < y[j]:
            y[j] = y[j] - x[i]
            SUM = SUM + x[i] * abs(i-j)
            x[i] = 0
            i = i + 1
        else:
            x[i] = x[i] - y[j]
            SUM = SUM + y[j] * abs(i-j)
            y[j] = 0
            j = j + 1

    return SUM

def point_wasserstein(point0, point1):
    # accumulate the wasserstein distance of the histograms on two points
    total = 0
    macs = set(point0.keys()) & set(point1.keys())
    for mac in macs:
        total = total + hist_wasserstein_distance(point0[mac],point1[mac])
    return total/len(macs)

def point_jaccard(point0, point1):
    total = 0
    macs = set(point0.keys()) & set(point1.keys())
    for mac in macs:
        total = total + hist_jaccard(point0[mac],point1[mac])
    return total/len(macs)

def point_euclid(point0, point1):
    return math.sqrt((point0[0] - point1[0])**2 + (point0[1] - point1[
        1])**2 )

def assign_colors():
    r,g,b = colorlines.pop(0)
    return (round((r+1)/256.0,2),
            round((g+1)/256.0,2),
            round((b+1)/256.0,2)
            )

def parse_data_file(dataFile, coloring = True, normalize = False, hour = []):

    # hour in range(0, 24) to seperate the data from a specific hour
    with open(dataFile, 'r') as f:
        dataValue = {}
        dataTime = {}
        dataHist = {}
        dataPoints = {}
        dataColors = {}
        counter = 0
        # for matrix index mapping

        # readfile
        for line in f:
            each = line.split(',')
            point = (int(each[2]),int(each[3]))
            timeStamp = float(each[0])
            image = each[1].strip()
            rssi = int(each[5])
            mac = each[4].strip()

            t = time.localtime(timeStamp)
            h = t.tm_hour

            if hour and not h in hour:
                continue


            if point not in dataValue.keys():
                dataValue[point] = {}
                dataTime[point] = {}
                dataHist[point] = {}

            if not hour:
                if mac not in dataValue[point].keys():
                    dataValue[point][mac] = []
                    dataTime[point][mac] = []
                    dataHist[point][mac] = []

                dataValue[point][mac].append(rssi)
                dataTime[point][mac].append(timeStamp)
            else:
                if mac not in dataValue[point].keys():
                    dataValue[point][mac] = {}
                    dataTime[point][mac] = {}
                    dataHist[point][mac] = {}

                if h not in dataValue[point][mac].keys():
                    dataValue[point][mac][h] = []
                    dataTime[point][mac][h] = []
                    dataHist[point][mac][h] = []

                dataValue[point][mac][h].append(rssi)
                dataTime[point][mac][h].append(timeStamp)

            if coloring:
                if mac not in dataColors.keys():
                    dataColors[mac] = assign_colors()

        if f:
            print("Data file loaded "+ dataFile)
        else:
            print("Incompatible data file: " + dataFile)

    for point in dataHist.keys():
        dataPoints[point] = counter
        for mac in dataHist[point].keys():
            if not hour:
                dataHist[point][mac], bins = hist_from_data(dataValue[point][mac],
                                                       (rssi_start, rssi_end))
                if normalize:
                    dataHist[point][mac] = hist_normalize(dataHist[point][mac])
            else:
                for h in hour:
                    dataHist[point][mac][h], bins = \
                        hist_from_data(
                            dataValue[point][mac][h],(rssi_start, rssi_end))
                    if normalize:
                        dataHist[point][mac][h] = \
                            hist_normalize(dataHist[point][mac][h])
        counter = counter + 1
    return dataValue, dataTime, dataHist, bins, dataColors

def freq_hourly(dataValue, dataTime):
    freqHourly = {}
    hour = 60 * 60
    for point in dataValue.keys():
        for mac in dataValue[point].keys():
            if not mac in freqHourly.keys():
                freqHourly[mac] = {}
            for i in range(0,len(dataValue[point][mac])):
                # if flag:
                #     start = dataTime[point][mac][i]
                    # # print time.strftime("%H:%M", time.gmtime(int(
                    # # start)-time.timezone))
                    # flag = False
                t = time.localtime(dataTime[point][mac][i])
                h = t.tm_hour
                if not t.tm_hour in freqHourly[mac].keys():
                    freqHourly[mac][h] = 0
                freqHourly[mac][h] = freqHourly[mac][h] + 1

    # print freqHourly

def hist_interpolation_test(t):
    i = 20
    j = 5
    x = .4
    y = .5
    k0 = i + t * (j-i)
    k1 = j + t * (i-j)
    if x > y:
        tmp = y
    else:
        tmp = x

    print(k0, k1)
    print((1-t) * tmp, t * tmp)


def parse_hst_file(hstFile, coloring = True):
    # returns a dictionary object with
    # points |
    #        -> mac |
    #                -> histogram

    dataColors = {}
    dataHist = {}
    with open(hstFile, 'r') as f:
        for line in f:
            lineArr = line.split(":",1)
            if lineArr[0] == "Fingerprints":
                dataTemp = json.loads(lineArr[1])
                for pts in dataTemp.keys():
                    tuplePts = literal_eval(pts)
                    dataHist[tuplePts] = {}
                    for mac in dataTemp[pts]:
                        hist = dataTemp[pts][mac]
                        dataHist[tuplePts][mac] = hist

            elif lineArr[0] == "Bins":
                bins = json.loads(lineArr[1])
            elif lineArr[0] == "Beacons":
                beacons = {}
                beaconsTemp = json.loads(lineArr[1])
                for mac in beaconsTemp.keys():
                    beacons[mac] = beaconsTemp[mac][0]
                    if coloring:
                        dataColors[mac] = beaconsTemp[mac][1]
            else:
                print "Invalid file"
                return None



    return dataHist, bins, beacons, dataColors

def find_closest_points(point, pointList, radius = 1.25, numMax = 0):
    # return the <numMax> points that are in the circle of radius <radius> in
    #  meters
    closest = []
    retClose = []
    for otherPoint in pointList:
        dist = point_euclid(otherPoint, point)
        if dist == 0:
            continue
        if dist < radius:
            closest.append((otherPoint, dist))

    closest = sorted(closest, key=lambda pair: pair[1])
    counter = 0
    for i in closest:
        retClose.append(i[0])
        counter += 1
        if not numMax == 0:
            if counter == numMax:
                break
    return retClose

def find_best_pair(point, pairs):
    # find the closest point pair that are aligned with the point
    # should return only the best pair
    # should return a list of pairs (with only one pair in it)
    if len(pairs) == 0:
        return ()
    minDist = 50.0
    selectedPair = [pairs[0]]
    for pair in pairs:
        midpoint = ((pair[0][0] + pair[1][0])/2, (pair[0][0] + pair[1][0])/2)
        dist = point_euclid(point, midpoint)
        if dist < minDist:
            minDist = dist
            selectedPair = pair

    return selectedPair

def find_all_pairs(point, pointList, ori = None, tol = .05, align = 0.2):
    # find all the closest pairs that are aligned with the point
    # with specific orientation (if given)
    combs = combinations(pointList,2)
    retCombs = []
    if not ori == None:
        if ori + 1 < tol:
            tolRange = [ori - tol + 2, ori + tol]
        else:
            if 1 - ori < tol:
                tolRange = [ori - tol, ori + tol - 2]
            else:
                tolRange = [ori - tol, ori + tol]

    for comb in combs:
        if are_aligned(point,comb[0], comb[1], th = align):
            if not ori == None:
                sampleOri =  orientation(comb[0],comb[1])
                if tolRange[1] < tolRange[0]: # different edges
                    if sampleOri < tolRange[1] or sampleOri > tolRange[0]:
                        retCombs.append(comb)
                else:
                    if tolRange[0] < sampleOri and sampleOri < tolRange[1]:
                        retCombs.append(comb)
            else:
                retCombs.append(comb)
    return retCombs

def calculate_t(pointx, point1, point2, type = 'linear'):
    # t estimation via distance to the fingerprints
    dist1 = point_euclid(pointx, point1)
    dist2 = point_euclid(pointx, point2)
    dist0 = point_euclid(point1, point2)

    if type == 'linear':
        d1 = dist1
        d2 = dist2
        d0 = dist0
    elif type == 'quad':
        d1 = dist1**2
        d2 = dist2**2
        d0 = dist0**2
    elif type == 'log':
        d1 = math.log(dist1)
        d2 = math.log(dist2)
        d0 = math.log(dist0)
    elif type == 'exp':
        d1 = math.exp(dist1)
        d2 = math.exp(dist2)
        d0 = math.exp(dist0)
    elif type == 'cubic':
        d1 = dist1**3
        d2 = dist2**3
        d0 = dist0**3
    else:
        print "No type mapping supplied."
        sys.exit(0)

    if d1 >= d0:
        return d1/d0

    if d2 >= d0:
        return -d1/d0

    return d1 / d0

def are_aligned(interpoint, point0, point1, th = 0.2):
    # check if three points are aligned
    # threashold is the length of the normal to the point0-point1 segment

    lengthNormal = abs((point1[1] - point0[1])* interpoint[0]
        - (point1[0] - point0[0]) * interpoint[1]
        + point1[0] * point0[1] - point1[1] * point0[0]) \
    / math.sqrt((point1[1] - point0[1])**2
                + (point1[0] - point0[0])**2
    )
    if lengthNormal < th:
        return True
    else:
        return False


def orientation(point0, point1):
    # returns the orientation as a scale in [-1, 1]
    if point1 == point0:
        return None
    if point1[0] == point0[0]:
        return 1.0

    return math.atan((point1[1] - point0[1]) / (point1[0] - point0[0]))/\
           math.pi * 2


def get_wasserstein_vs_beta(dataHist, beacon, radius = 10.0, bStep = .01):
    print beacon
    # find the likelihood p(data|beta) using all available points
    betas = range(0,int(1.0/bStep) + 1)
    wassBeta = {}

    for point in dataHist.keys():
        # we set the radius very big to get all the other points
        closest = find_closest_points(point,dataHist.keys(),radius = radius)

        # find all the aligned point pairs
        all_aligned_pairs = find_all_pairs(point, closest)

        if len(all_aligned_pairs) == 0:
            print point, " empty"
            continue
        print point

        if not beacon in dataHist[point].keys():
            continue
        for pair in all_aligned_pairs:
            # take two points that are in range and aligned with the point
            # calculate t for the current point and pair
            t = calculate_t(point, pair[0], pair[1])
            if not beacon in dataHist[pair[0]].keys() or\
                not beacon in dataHist[pair[1]].keys():
                continue

            # find the wasserstein mapping for the current pair
            s, mapping = hist_wasserstein(
                dataHist[pair[0]][beacon],
                dataHist[pair[1]][beacon])
            # group the orientations
            ori = round(int(orientation(pair[0],pair[1])/bStep)*bStep,3)
            if (point[0], point[1], ori) not in wassBeta.keys():
                wassBeta[(point[0], point[1], ori)] = []
            wassBeta[(point[0], point[1], ori)].append(
                [0] * len(betas)
            )
            for i in betas:
                # generate the interpolation at t, beta
                tempHist = hist_wasserstein_interpolation(
                    mapping,
                    t,
                    float(i)/float(betas[-1]))

                # calculate the wasserstein distance
                S,M = hist_wasserstein(tempHist, dataHist[point][beacon])
                wassBeta[(point[0], point[1], ori)][-1][i] = S

    # second pass, take the mean of the W values
    for eachPoint in wassBeta.keys():
        counter = 0
        tempList = [0]*len(betas)
        for listItem in wassBeta[eachPoint]:
            tempList = map(add, tempList, listItem)
            counter += 1
        for i in range(len(betas)):
            tempList[i] = round(tempList[i] / float(counter),3)

        # find argmin
        minimum = tempList[0]
        minIndex = 0
        for i in range(1,len(betas)):
            if tempList[i] < minimum:
                minimum = tempList[i]
                minIndex = i
        wassBeta[eachPoint] = (tempList, round(minIndex*bStep,3))
    return wassBeta


def sampleRandomPoint2dUniform(rect):
    # Generate random points given the area
    return (round(random.uniform(rect[0][0], rect[1][0]),3),
            round(random.uniform(rect[0][1], rect[1][1]),3))

def sampleRandomPoint2dNormal(point, sigma):
    # Generate random points given a reference point and a variance
    return (random.normalvariate(point[0], sigma),
           random.normalvariate(point[1], sigma))

def generateBetaFile(fileName, data, beacons):
    bStep = .1
    for beacon in beacons.keys():
        wassBeta = get_pairs_vs_beta(data, beacon, bStep = bStep)


        with open(fileName, 'a+') as f:
            f.write("Beacon: " + beacon + "\n")
            print "Writing to file: "  + fileName
            for each in wassBeta.keys():
                json.dump(each,f)
                f.write(":")
                json.dump(wassBeta[each],f)
                f.write("\n")

def betaParser(dataFile):
    data = {}
    with open(dataFile, 'r') as f:
        for line in f:
            lineItems = line.split(":", 1)
            if lineItems[0] == "Beacon":
                beacon = lineItems[1].strip()
                data[beacon] = {}
            else:
                dataPoint = literal_eval(lineItems[0].strip())
                dataList = literal_eval(lineItems[1].strip())
                # print dataPoint
                if dataList:
                    data[beacon][(dataPoint[0],
                                  dataPoint[1],
                                  dataPoint[2])] = dataList
    return data


def randgen(cumul_vector, sampleSize, pattern = None):
    # generate a random value given a discrete vector of probabilities
    # pattern should have the same size with prob_vector

    ret = [None] * sampleSize

    for j in range(sampleSize):
        ret[j] = sampleFrom(cumul_vector, pattern)

    return ret


def getCumulative(prob_vector):
    # prepare the cumulative sum for inversion
    cumulative = list(np.cumsum(prob_vector))
    s = float(cumulative[-1])

    # normalize
    for i in range(len(cumulative)):
        cumulative[i] = cumulative[i]/s

    return cumulative


def sampleFrom(cumulative, pattern = None):
    rnd = random.uniform(0, 1)
    for i in range(len(cumulative)):
        if rnd <= cumulative[i]:
            if pattern == None:
                ret = i
            else:
                ret = pattern[i]
            break

    return ret

def distance_matrix(dataHist):
    # generate a distance matrix given the dataHist type
    distMatrix = np.zeros([len(dataHist.keys()), len(dataHist.keys())])
    mapPoints = {}
    for i in range(len(dataHist.keys())):
        mapPoints[dataHist.keys()[i]] = i
        for j in range(len(dataHist.keys())):
            distMatrix[i,j] = point_euclid(
                    dataHist.keys()[i], dataHist.keys()[j]
            )

    return distMatrix, mapPoints

def write_grids(dataHist, beacons, limits, sizeGrid, fileName, beta = 0.38,
                delimiter = "::"):
    # self.lQueue.put("ParticleFilter: Preparing grids with size " + str(
    #         self.sizeGrid))
    # cells = []
    # cellsInv = {}

    # divide the world into grids
    widthGrid =  int(np.ceil(
            limits[1][0]/sizeGrid)) + 1
    heightGrid = int(np.ceil(
            limits[1][1]/sizeGrid)) + 1

    hist = np.zeros(rssi_end - rssi_start)
    header = str(limits) + delimiter + str(sizeGrid) + "\n"
    f = open(fileName, "w+")
    f.write(header)

    # generate cellVisuals
    for j in range(heightGrid):
        for i in range(widthGrid):
            point = (round(limits[0][0] + i
                           *sizeGrid,2),
                     round(limits[0][1] + j
                           *sizeGrid,2) )
            # cellsInv[point] = i + j * widthGrid
            # cells.append({})

            pointList = find_closest_points(point,
                                            dataHist.keys(),
                                            radius=15.0)
            pairs = find_all_pairs(point, pointList, align = 0.53)
            if len(pairs) == 0:
                continue

            print j, i, len(pairs)

            for beacon in beacons.keys():
                # print beacon
                hists = []
                weights = []
                for pair in pairs:
                    # get t value for the triplet
                    S, mapping = hist_wasserstein(
                        dataHist[pair[0]][beacon],
                        dataHist[pair[1]][beacon]
                    )

                    t = calculate_t(point, pair[0], pair[1])
                    hist = hist_wasserstein_interpolation(mapping, t, beta)
                    hists.append(hist)

                    distPair = (point_euclid(point, pair[0]) +
                                point_euclid(point, pair[1]))
                    weights.append(np.exp(-distPair))

                histInterp = \
                    hist_multiple_convex_combination(hists, weights)

                # cells[-1][beacon] = histInterp
                f.write(str(list(point)) + delimiter  +\
                    str(j) + delimiter + \
                    str(i) + delimiter + \
                    str(beacon) + delimiter + \
                    str(list(histInterp)) + "\n")

    f.close()

    # self.lQueue.put("ParticleFilter: Prepared grids.")

def read_grids(fileName, delimiter = "::", lQueue = None):

    if lQueue:
        lQueue.put("ParticleFilter: Reading grids from file.")
    else:
        print "ParticleFilter: Reading grids from file."

    # open file and read the header
    f = open(fileName, "r")

    line = f.readline()
    lineList = line.strip().split(delimiter)
    limits = json.loads(lineList[0])
    sizeGrid = json.loads(lineList[1])


    widthGrid =  int(np.ceil(
            limits[1][0]/sizeGrid)) + 1
    heightGrid = int(np.ceil(
            limits[1][1]/sizeGrid)) + 1

    # allocate a big list
    cells = [ None ] * widthGrid * heightGrid
    cellsInv = {}

    for line in f:
        lineList = line.strip().split(delimiter)
        point = tuple(json.loads(lineList[0]))
        j = int(lineList[1])
        i = int(lineList[2])
        index = j * widthGrid + i
        hist = json.loads(lineList[4])
        beacon = lineList[3]
        cellsInv[point] = i + j * widthGrid
        if cells[index] == None:
            cells[index] = {}

        cells[index][beacon] = np.array(hist)

    f.close()

    if lQueue:
        lQueue.put("ParticleFilter: Prepared grids.")
    else:
        print "ParticleFilter: Prepared grids."

    return cells, cellsInv, widthGrid, heightGrid, sizeGrid

def kernel_gauss(x1,x2, params = None):
    # x1, x2 being np row vectors of size N
    return np.exp(- .5 * np.dot((x1-x2), np.transpose(x1-x2)))

def kernel_gauss_ebden(x1,x2, params):
    # params = [ sigma_f, l, sigma_N ]
    # x1, x2 being np row vectors of size N
    return params[0]**2 *\
           np.exp(-(.5/(params[1]**2)) * np.dot((x1-x2), np.transpose(
                   x1-x2))) + params[2]**2

def kernel_block_dist(x1,x2, params = None):
    # x1, x2 being np row vectors of size N
    return np.exp(-.5* np.sqrt(np.dot((x1-x2), np.transpose(x1-x2))))

def compute_K(X,Y, kernel, params):
    S = np.zeros([len(X), len(Y)])
    for i in range(len(X)):
        for j in range(len(Y)):
            S[i][j] = kernel(X[i], Y[j], params)
    return S

def gpr(X,Y,xin, K = None, sigma = None, kernel = kernel_gauss,
        params = (1.0, 1.0, 0.3)):
    if K == None:
        K = compute_K(X,X, kernel, params) + \
            np.identity(len(X)) * params[2] ** 2

    Ks = compute_K(xin,X, kernel, params)
    Kss = compute_K(xin,xin, kernel, params)
    mean = np.dot(
            Ks, np.dot(np.linalg.inv(K),Y)
    )
    if sigma == None:
        sigma = Kss - np.dot(np.dot(Ks, np.linalg.inv(K)),
                         np.transpose(Ks))

    return mean, sigma, K

def gpr_prepare_fingerprint(dataHist, beacon, rssi_index):
    N = len(dataHist)

    X = np.zeros([N, 2]) # locations
    Y = np.zeros([N, 1]) # values

    for i in range(N):
        X[i] = [ dataHist.keys()[i][0], dataHist.keys()[i][1]]
        Y[i] = [ dataHist[dataHist.keys()[i]][beacon][rssi_index] ]

    return X, Y

def gpr_prepare_maxRSSI(dataHist, beacon):
    N = len(dataHist)

    X = np.zeros([N, 2]) # locations
    Y = np.zeros([N, 1]) # values

    for i in range(N):
        X[i] = [ dataHist.keys()[i][0], dataHist.keys()[i][1]]
        Y[i] = [ np.argmax(dataHist[dataHist.keys()[i]][beacon]) + rssi_start ]

    return X, Y

