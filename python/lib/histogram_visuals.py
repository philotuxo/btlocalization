import matplotlib
matplotlib.use("Qt4Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_pdf import PdfPages
from histograms import *
from PyQt4 import QtCore
from mpl_toolkits.mplot3d import Axes3D

def int2rgb(rgbint):
    # convert the 24 bit color into seperate color codes
    # color codes in [0, 255]
    b = rgbint & 255
    g = (rgbint >> 8) & 255
    r = (rgbint >> 16) & 255
    return (r,g,b)

def rgb2int(rgb):
    # convert seperate color codes to 24bit (of course the color info is lost)
    return int(((rgb[0])) * 65536 + (rgb[1]) * 256 + (rgb[2]))


def real2Pix(params, coord):
    # take the real coordinates of a point, convert it to pixel coordinates

    if params["direction"] and \
        params["origin"] and \
        params["parity"]:
        return QtCore.QPoint(
            round(params["direction"].x() / \
            params["parity"] * \
            coord[0] + params["origin"].x()),
            round(params["direction"].y() / \
            params["parity"] * \
            coord[1] + params["origin"].y()))
    else:
        return QtCore.QPoint(0,0)

def pix2Real(params, pixCoord):
    # take the pixel coordinates of a point, convert it to real coordinates
    if params["direction"] and \
        params["origin"] and \
        params["parity"]:
        return params["direction"].x() * (pixCoord.x() - params[
                "origin"].x()) * params["parity"], \
                params["direction"].y() * (pixCoord.y() - params[
                "origin"].y()) * params["parity"], \
                0
    else:
        return 0,0,0

def hist_plot(hist, bins, color = None, outputFile = None, yRange = None,
              xRange = None):
    if not color:
        color = [0,0,1]

    if xRange:
        xRange = [ xRange[0] - bins[0], xRange[1] - bins[0] ]
        fig = plt.bar(bins[xRange[0]:xRange[1]],
                      hist[xRange[0]:xRange[1]], color = color)
    else:
        fig = plt.bar(bins[:-1],hist, color = color)
    a = plt.gca()
    a.axes.get_xaxis().set_ticklabels([])
    a.axes.get_xaxis().grid()
    # a.axes.get_yaxis().set_ticks([])
    # plt.xlim([-100, -70 ])
    if yRange:
        plt.ylim(yRange)
    if outputFile:
        pp = PdfPages(outputFile)
        plt.savefig(pp, format='pdf')
        pp.close()
        print "Current figure saved to: " + outputFile


def save_point_plot(dataHist, bins, point, colors, outputFile = None, beacons =
None):
    # plot all the available histograms on the point
    plt.clf()
    if beacons:
        subSize = len(beacons)
    else:
        subSize = len(dataHist[point].keys())

    plt.figure(figsize=(8, 4))
    counter = 1
    for mac in colors.keys():
        if mac not in dataHist[point].keys():
            continue
        if beacons:
            if mac not in beacons:
                continue
        plt.subplot(subSize,1,counter)
        if counter == 1:
            plt.title(str(point))
        fig = plt.bar(bins[:-1],dataHist[point][mac], color = colors[mac])
        plt.subplots_adjust(hspace = 0.001)
        a = plt.gca()
        if not counter == subSize:
            a.axes.get_xaxis().set_ticklabels([])
        a.axes.get_xaxis().grid()
        a.axes.get_yaxis().set_ticks([])
        plt.xlim([-100, -70 ])
        plt.ylim([0,1])
        counter += 1
    if outputFile:
        pp = PdfPages(outputFile)
        plt.savefig(pp, format='pdf')
        pp.close()
        print "Current figure saved to: " + outputFile
    else:
        plt.show()
    plt.close()


def hist_plot_pairwise(hist0, hist1, bins):
    plt.hold(True)
    plt.bar(bins[:-1],hist0, color = (1,0,0,.125))
    plt.bar(bins[:-1],hist1, color = (0,1,0,.125))
    # plt.hold(False)

def hist_plot_interpolation(hist0, hist1, bins, mapping,
                            tStep = .2, betaStep = .2,
                            method = hist_wasserstein_interpolation):
    TSIZE = int(1/tStep) + 1
    BETASIZE = int(1/betaStep) + 1

    plt.figure()
    M0 = max(hist0)
    M1 = max(hist1)
    M = max(M0,M1)
    plt.ylim([0,M])

    for i in range(0,TSIZE):
        for j in range(0,BETASIZE):
            plt.subplot(BETASIZE,TSIZE,(j * TSIZE + i) + 1)
            plt.hold(True)
            hist = method(mapping, i*tStep,j* betaStep)
            # print i*stepsize, j*stepsize
            # hist_plot_pairwise(hist0, hist1, bins)
            plt.bar(bins[:-1], hist, color = (0,0,1,.75))
            a = plt.gca()
            a.axes.get_xaxis().set_ticks([])
            a.axes.get_yaxis().set_ticks([])
            plt.title(r'$ t $' + " = %s," % (i*tStep) +
                      r'$ \beta $' + " = %s" % (j* betaStep),
                      fontsize=10)
            plt.ylim([0,M])


def hist_plot_extrapolation(hist0, hist1, bins, mapping,
                            tStep = .2, betaStep = .2,
                            method = hist_wasserstein_interpolation,
                            landmark = [-100, -80]):

    TSIZE = int(1/tStep) + 5
    BETASIZE = int(1/betaStep) + 1

    plt.figure()
    M0 = max(hist0)
    M1 = max(hist1)
    M = max(M0,M1)
    plt.ylim([0,M])

    for i in range(0,TSIZE):
        for j in range(0,BETASIZE):
            plt.subplot(BETASIZE,TSIZE,(j * TSIZE + i) + 1)
            plt.hold(True)
            hist = method(mapping, (i-2)*tStep,j* betaStep,
                          limits= (bins[0],bins[-1]))
            # print i*stepsize, j*stepsize
            # hist_plot_pairwise(hist0, hist1, bins)
            plt.bar(bins[:-1], hist, color = (0,0,1,.75))
            a = plt.gca()
            a.axes.get_xaxis().set_ticks([])
            a.axes.get_yaxis().set_ticks([])
            plt.title(r'$ t $' + " = %s," % ((i-2)*tStep) +
                      r'$ \beta $' + " = %s" % (j* betaStep),
                      fontsize=10)
            plt.ylim([0,M])
            plt.xlim([bins[0],bins[-1]])
            plt.plot([landmark[0],landmark[0]], [0,M], '-y')
            plt.plot([landmark[1],landmark[1]], [0,M], '-y')



def draw_hist_hourly(dataValue,dataTime,bins,dataColors):
    histHourly = {}
    flag = True

    # generate separate histograms for each hour
    for point in dataValue.keys():
        for mac in dataValue[point].keys():
            if not mac in histHourly.keys():
                histHourly[mac] = {}
            for i in range(0,len(dataValue[point][mac])):
                if flag:
                    start = dataTime[point][mac][i]
                    formatted = time.localtime(start)
                    flag = False
                t = time.localtime(dataTime[point][mac][i])
                h = t.tm_hour
                if not t.tm_hour in histHourly[mac].keys():
                    histHourly[mac][h] = np.zeros(rssi_end - rssi_start)

                histHourly[mac][h][dataValue[point][mac][i] + 120] += 1

    # normalize hourly
    for mac in histHourly.keys():
        for h in histHourly[mac].keys():
            histHourly[mac][h] = histHourly[mac][h]/ sum(histHourly[mac][h])


    # plot hourly
    for mac in histHourly.keys():
        for h in histHourly[mac].keys():
            plt.subplot(8,3,h+1)
            plt.hold(True)
            plt.bar(bins[:-1],histHourly[mac][h], color = dataColors[mac])
            a = plt.gca()
            # a.axes.get_xaxis().set_ticks([])
            a.axes.get_yaxis().set_ticks([])
            plt.title("Hour: %s" % (h), fontsize=8)


def draw_rssi_bars(dataHist, beacon, rssi_index):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    xpos = []
    ypos = []
    dz = []
    dx = []
    dy = []
    zpos = []

    for point in dataHist.keys():
        xpos.append(point[0])
        ypos.append(point[1])
        dz.append(dataHist[point][beacon][rssi_index])
        dx.append(.25)
        dy.append(.25)
        zpos.append(0)

    ax.bar3d(xpos, ypos, zpos, dx, dy, dz, color='g', alpha = .75)
    ax.set_zlim(0,1)

    ax.set_title(beacon)

    plt.show()

def gpr_test():

    X = np.matrix([[-1.50], [-1], [-.75], [-.40], [-.25], [0]])

    Y = np.matrix([[-1.6], [-1.1], [-.4], [.2], [.5], [.8]])


    fig = plt.figure()
    ax = fig.gca()

    x1 = np.arange(-1.6, 0.2, .01)
    len1 = len(x1)
    output = np.zeros([len1, 1])
    conf1 = np.zeros([len1, 1])
    conf2 = np.zeros([len1, 1])

    K = None
    for i in range(len1):
        # print i
        output[i], sigma, K = gpr(X,Y, np.array([[ x1[i]]]), kernel =
        kernel_gauss, params = [1.0, 1.0, 0.3], K = K )
        conf1[i] = output[i] +  1.96 * np.sqrt(sigma)
        conf2[i] = output[i] -  1.96 * np.sqrt(sigma)

    surf1 = ax.plot(x1, output, 'k')
    surf2 = ax.plot(x1, conf1, 'b')
    surf3 = ax.plot(x1, conf2, 'b')


    # plt.plot(input, output, 'b')
    ax.plot(X,Y,'k+')

    plt.show()

def gpr_test_2d():

    X = np.matrix([[-1.50, 3],
                   [-1, 2.5],
                   [.25, 2],
                   [.40, 1.5],
                   [-.25, 1],
                   [0, 0.5],
                   [-.85, 0.4]])

    Y = np.matrix([[1], [1], [1], [1], [1], [1], [1]])

    fig = plt.figure()
    ax = fig.gca(projection='3d')

    x1 = np.arange(-1.6, 0.2, .1)
    x2 = np.arange(0.25, 3.25, .1)
    len1 = len(x1)
    len2 = len(x2)
    print len1, len2
    output = np.zeros([ len2, len1])
    conf1 = np.zeros([ len2, len1])
    conf2 = np.zeros([ len2, len1])
    x1, x2 = np.meshgrid(x1, x2)


    for i in range(len2):
        print i
        for j in range(len1):
            output[i][j], sigma, K = gpr(X,Y, np.array([[ x1[i][j], x2[i][j]
                                                        ]]),.5 )
            conf1[i][j] = output[i][j] +  sigma
            conf2[i][j] = output[i][j] -  sigma

    surf1 = ax.plot_surface(x1, x2, output, rstride=1, cstride=1, cmap=cm.coolwarm,
                           linewidth=0, antialiased=False)
    surf2 = ax.plot_wireframe(x1, x2, conf1, rstride=2, cstride=2, color = 'y',
                           linewidth=.001, antialiased=False)

    surf3 = ax.plot_wireframe(x1, x2, conf2, rstride=2, cstride=2, color = 'y',
                           linewidth=.001, antialiased=False)

    for i in range(len(X)):
        ax.scatter(X[i,0], X[i,1], Y[i,0], 'ko')

    # plt.plot(input, output, 'b')
    # plt.plot(X,Y,'k.')

    plt.show()


def gpr_surface_fingerprints(dataHist, beacon, rssi_index, area_rect,
                             res = .5):
    # create an input vector for gpr

    X, Y = gpr_prepare_fingerprint(dataHist, beacon, rssi_index)

    x1 = np.arange(area_rect[0], area_rect[1], res)
    x2 = np.arange(area_rect[2], area_rect[3], res)

    area_length = len(x1)
    area_width = len(x2)

    mean_surface = np.zeros([ area_width, area_length])
    confidence_mesh_plus = np.zeros([ area_width, area_length])
    confidence_mesh_minus = np.zeros([ area_width, area_length])
    grid_x1, grid_x2 = np.meshgrid(x1, x2)

    K = None

    for i in range(area_width):
        print i
        for j in range(area_length):
            mean_surface[i][j], sigma, K = gpr(X, Y,
                    np.array([[ grid_x1[i][j], grid_x2[i][j] ]]), K = K)
            confidence_mesh_plus[i][j] = mean_surface[i][j] +  3* sigma
            confidence_mesh_minus[i][j] = mean_surface[i][j] - 3* sigma

    fig = plt.figure()
    ax = fig.gca(projection='3d')

    stride = int(.5/res)

    surf1 = ax.plot_surface(grid_x1, grid_x2, mean_surface, rstride=1, cstride=1,
                            cmap=cm.coolwarm,
                           linewidth=0, antialiased=False)
    surf2 = ax.plot_wireframe(grid_x1, grid_x2, confidence_mesh_plus,
                              rstride=stride, cstride=stride,color = 'y',
                           linewidth=1, antialiased=False)

    surf3 = ax.plot_wireframe(grid_x1, grid_x2, confidence_mesh_minus,
                              rstride=stride, cstride=stride, color = 'y',
                           linewidth=1, antialiased=False)
    for i in range(len(X)):
        ax.scatter(X[i,0], X[i,1], Y[i,0], 'k+', linewidth = 2)


    plt.show()


def gpr_surface_maxRssi(dataHist, beacon, area_rect, res = .5):
    # create an input vector for gpr

    X, Y = gpr_prepare_maxRSSI(dataHist, beacon)

    x1 = np.arange(area_rect[0], area_rect[1], res)
    x2 = np.arange(area_rect[2], area_rect[3], res)

    area_length = len(x1)
    area_width = len(x2)

    mean_surface = np.zeros([ area_width, area_length])
    confidence_mesh_plus = np.zeros([ area_width, area_length])
    confidence_mesh_minus = np.zeros([ area_width, area_length])
    grid_x1, grid_x2 = np.meshgrid(x1, x2)

    K = None

    for i in range(area_width):
        print i
        for j in range(area_length):
            mean_surface[i][j], sigma, K = gpr(X, Y,
                    np.array([[ grid_x1[i][j], grid_x2[i][j] ]]), K = K,
                                               kernel= kernel_gauss_ebden,
                                               params=(1.0,.5,1))
            confidence_mesh_plus[i][j] = mean_surface[i][j] +  3* sigma
            confidence_mesh_minus[i][j] = mean_surface[i][j] - 3* sigma

    fig = plt.figure()
    ax = fig.gca(projection='3d')

    stride = int(.5/res)

    surf1 = ax.plot_surface(grid_x1, grid_x2, mean_surface, rstride=1, cstride=1,
                            cmap=cm.coolwarm,
                           linewidth=0, antialiased=False)
    surf2 = ax.plot_wireframe(grid_x1, grid_x2, confidence_mesh_plus,
                              rstride=stride, cstride=stride,color = 'y',
                           linewidth=.1, antialiased=False)

    surf3 = ax.plot_wireframe(grid_x1, grid_x2, confidence_mesh_minus,
                              rstride=stride, cstride=stride, color = 'y',
                           linewidth=.1, antialiased=False)
    for i in range(len(X)):
        ax.scatter(X[i,0], X[i,1], Y[i,0], 'k+', linewidth = 2)


    plt.show()
