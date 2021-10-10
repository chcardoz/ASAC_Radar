from os import sep
from airsim.types import LidarData
from numpy.core.fromnumeric import size
from pandas.io.formats import style
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pandas as pd
from pyqtgraph.functions import colorStr
from scipy.spatial.transform import Rotation as R
from sklearn import cluster
from sklearn.cluster import DBSCAN
from re import search
import airsim
import sys


class RadarPlot():
    def __init__(self):
        # QT visualization setup
        self.traces = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.win = pg.GraphicsLayoutWidget(title="Hello There", show=True)
        self.win.resize(600, 600)
        self.win.setWindowTitle('ASAC Radar')
        self.t = np.arange(0, 3.0, 0.01)
        pg.setConfigOptions(antialias=True)
        self.canvas = self.win.addPlot()

        # File writing index
        self.file_idx = 0

        # DBSCAN variables
        self.epsilon = 1
        self.minimum_samples = 20

        # Connecting to Airsim
        self.client = airsim.CarClient()
        self.client.confirmConnection()
        self.client.enableApiControl(True)
        self.car_controls = airsim.CarControls()

    def trace(self, name, dataset_x, dataset_y):
        if name in self.traces:
            self.traces[name].setData(dataset_x, dataset_y)
        else:
            if name == "origin":
                self.traces[name] = self.canvas.plot(
                    pen=None, symbol='o', symbolPen=None, symbolSize=20, symbolBrush=(207, 0, 15, 255))
            elif name == "radar":
                self.traces[name] = self.canvas.plot(
                    pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=(30, 130, 76, 50))
            elif name == "centroid":
                self.traces[name] = self.canvas.plot(
                    pen=None, symbol='x', symbolPen=None, symbolSize=15, symbolBrush=(255, 255, 255, 255))
            elif name == "corepoint":
                self.traces[name] = self.canvas.plot(
                    pen=None, symbol='o', symbolPen=None, symbolSize=15, symbolBrush=(46, 204, 113, 100))
            self.canvas.setXRange(-40, 40)
            self.canvas.setYRange(0, 60)

    def update(self):
        file_name = "RadarData\Radar" + str(self.file_idx) + ".txt"
        self.radarData = self.client.getLidarData(lidar_name="LidarSensor")
        if (len(self.radarData.point_cloud) < 3):
            print("\tNo points received from the Radar sensor")
        else:
            self.radarPoints = self.parse_radarData(self.radarData)
            self.write_pointcloud_to_file()
            origin = np.array([[0, 0]])
            self.DBSCAN()

            self.trace(
                "radar", self.radarPoints[:, 1], self.radarPoints[:, 0])
            self.trace(
                "corepoint", self.corepoints[:, 1], self.corepoints[:, 0])
            self.trace(
                "centroid", self.corepoints_centroids['y'], self.corepoints_centroids['x'])
            self.trace("origin", origin[:, 1], origin[:, 0])
            self.file_idx += 1

    def DBSCAN(self):
        clustering = DBSCAN(eps=self.epsilon, min_samples=self.minimum_samples)
        clustering.fit(self.radarPoints)
        self.corepoints = self.radarPoints[clustering.core_sample_indices_, :]
        self.rotated_df['label'] = pd.DataFrame(clustering.labels_)
        self.corepoints_df = self.rotated_df[self.rotated_df['label'] != -1]
        self.corepoints_centroids = self.corepoints_df.groupby(
            ['label']).mean()

    def parse_radarData(data):
        points = np.array(data.point_cloud, dtype=np.dtype('f4'))
        points = np.reshape(points, (int(points.shape[0]/3), 3))
        return points

    def write_pointcloud_to_file(self):
        file_id = "AirsimRadarData\Radar"+str(self.file_idx)
        self.radarPoints.tofile(file_id, sep=',')


if __name__ == '__main__':
    import sys
    p = RadarPlot()
    timer = QtCore.QTimer()
    timer.timeout.connect(p.update)
    timer.start(20)
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
