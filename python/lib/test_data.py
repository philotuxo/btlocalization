__author__ = 'serhan'

from decimal import Decimal
import numpy as np

def test_data1():
    hist0 = np.array([
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
             0.0, 0.0002, 0.0018, 0.007, 0.0184, 0.0478, 0.0752, 0.1036,
             0.1032, 0.0748, 0.0434, 0.0184,0.005, 0.001, 0.0002, 0.00240,
             0.049, 0.2006, 0.203, 0.0430, 0.002, 0.0, 0.0, 0.0,  0.0, 0.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],np.dtype(Decimal))
    hist1 = np.array([
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
             0.0002, 0.0004, 0.0076, 0.0366, 0.1086, 0.2094,  0.2632, 0.2208,
             0.1048, 0.04260, 0.00560, 0.0002, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
             0.0, 0.0, 0.0],np.dtype(Decimal))
    bins0 = np.array([
            -120.0, -119.0, -118.0, -117.0, -116.0, -115.0, -114.0, -113.0,
            -112.0, -111.0, -110.0, -109.0, -108.0, -107.0, -106.0, -105.0,
            -104.0, -103.0, -102.0, -101.0, -100.0, -99.0, -98.0, -97.0,
            -96.0, -95.0, -94.0, -93.0, -92.0, -91.0, -90.0, -89.0, -88.0,
            -87.0, -86.0, -85.0, -84.0, -83.0, -82.0, -81.0, -80.0, -79.0,
            -78.0, -77.0, -76.0, -75.0, -74.0, -73.0, -72.0, -71.0, -70.0,
            -69.0, -68.0, -67.0, -66.0, -65.0, -64.0, -63.0, -62.0, -61.0,
            -60.0],np.dtype(Decimal))
    return hist0, hist1, bins0

def test_data2():
    hist0 = np.array(
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0002, 0.0014,
        0.00580, 0.0166, 0.0438,  0.0742, 0.11, 0.1046, 0.0828, 0.0752,
        0.2256, 0.219, 0.0394, 0.0014, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0] ,np.dtype(Decimal))
    hist1 = np.array(
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0002, 0.017, 0.2246, 0.528, 0.2136, 0.0164, 0.0002, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        np.dtype(Decimal))
    bins0 = np.array(
        [-120.0, -119.0, -118.0, -117.0, -116.0, -115.0, -114.0, -113.0,
        -112.0, -111.0, -110.0, -109.0, -108.0, -107.0, -106.0, -105.0,
        -104.0, -103.0, -102.0, -101.0, -100.0, -99.0, -98.0, -97.0,
        -96.0, -95.0, -94.0, -93.0, -92.0, -91.0, -90.0, -89.0, -88.0,
        -87.0, -86.0, -85.0, -84.0, -83.0, -82.0, -81.0, -80.0, -79.0,
        -78.0, -77.0, -76.0, -75.0, -74.0, -73.0, -72.0, -71.0, -70.0,
        -69.0, -68.0, -67.0, -66.0, -65.0, -64.0, -63.0, -62.0, -61.0, -60.0],
        np.dtype(Decimal))

    return hist0, hist1, bins0

def test_data3(i,j):
    hist0 = np.array(np.zeros(70),np.dtype(Decimal))
    hist1 = np.array(np.zeros(70),np.dtype(Decimal))

    hist0[i] = 1
    hist1[j] = 1
    bins0 = np.array(
        [-125.0, -124.0, -123.0, -122.0, -121.0,-120.0, -119.0, -118.0,
         -117.0, -116.0, -115.0, -114.0, -113.0, -112.0, -111.0, -110.0,
         -109.0, -108.0, -107.0, -106.0, -105.0, -104.0, -103.0, -102.0,
         -101.0, -100.0, -99.0, -98.0, -97.0, -96.0, -95.0, -94.0, -93.0,
         -92.0, -91.0, -90.0, -89.0, -88.0, -87.0, -86.0, -85.0, -84.0,
         -83.0, -82.0, -81.0, -80.0, -79.0, -78.0, -77.0, -76.0, -75.0,
         -74.0, -73.0, -72.0, -71.0, -70.0, -69.0, -68.0, -67.0, -66.0,
         -65.0, -64.0, -63.0, -62.0, -61.0, -60.0, -59.0, -58.0, -57.0,
         -56.0, -55.0 ],
        np.dtype(Decimal))

    return hist0, hist1, bins0
