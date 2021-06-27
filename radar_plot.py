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


class RadarPlot():
    def __init__(self):
        self.traces = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.win = pg.GraphicsLayoutWidget(title="Hello There", show=True)
        self.win.resize(600, 600)
        self.win.setWindowTitle('ASAC Radar')
        self.file_idx = 29
        self.t = np.arange(0, 3.0, 0.01)
        pg.setConfigOptions(antialias=True)
        self.canvas = self.win.addPlot()

        # DBSCAN variables
        self.epsilon = 1
        self.minimum_samples = 20

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
            else:
                self.traces[name] = self.canvas.plot(pen=pg.mkPen(
                    color='y', width=0.5, style=QtCore.Qt.DashLine))
            self.canvas.setXRange(-40, 40)
            self.canvas.setYRange(0, 60)

    def update(self):
        file_name = "Radar" + str(self.file_idx) + ".txt"
        self.corepoints_centroids = None
        self.read_headers(file_name)
        self.read_data(file_name)
        origin = np.array([[0, 0]])
        self.DBSCAN()

        for index, row in self.corepoints_centroids.iterrows():
            name = "centroid_line_"+str(index)
            self.trace(name, [0, row[1]], [0, row[0]])
        self.trace(
            "radar", self.radar_data_rotated[:, 1], self.radar_data_rotated[:, 0])
        self.trace(
            "corepoint", self.corepoints[:, 1], self.corepoints[:, 0])
        self.trace(
            "centroid", self.corepoints_centroids['y'], self.corepoints_centroids['x'])
        self.trace("origin", origin[:, 1], origin[:, 0])
        self.file_idx += 1
        if(self.file_idx > 500):
            self.file_idx = 29

    def file_slice(self, file_name):
        file = open(file_name, "r")
        file_len = 0
        idx = 0
        found = False
        Content = file.read()
        CoList = Content.split("\n")

        for i in CoList:
            if i:
                file_len += 1
            if search(']', i) and (not found):
                found = True
                idx = file_len

        file.close()
        return idx, file_len

    def read_data(self, file_name):
        idx, file_len = self.file_slice(file_name)
        self.df = pd.read_table(file_name, names=[
                                'x', 'y', 'z'], skiprows=6, skipfooter=file_len-idx+2, delim_whitespace=True, engine='python', header=None)
        self.df = self.df - self.radarPosition
        self.radar_data = self.df.to_numpy()
        self.radar_data_rotated = self.rotation_matrix.dot(self.radar_data.T).T
        self.rotated_df = pd.DataFrame(
            self.radar_data_rotated, columns=['x', 'y', 'z'])

    def read_headers(self, file_name):
        file1 = open(file_name, 'r')
        for i, line in enumerate(file1):
            if i == 3:
                self.quaternion = np.array(line.split()[3:]).astype(float)
            elif i == 2:
                self.radarPosition = np.array(line.split()[3:]).astype(float)
        self.inverse_quat = np.negative(self.quaternion)
        self.r = R.from_quat(self.inverse_quat)
        self.rotation_matrix = self.r.as_matrix()
        file1.close()

    def DBSCAN(self):
        clustering = DBSCAN(eps=self.epsilon, min_samples=self.minimum_samples)
        clustering.fit(self.radar_data_rotated)
        self.corepoints = self.radar_data_rotated[clustering.core_sample_indices_, :]
        self.rotated_df['label'] = pd.DataFrame(clustering.labels_)
        self.corepoints_df = self.rotated_df[self.rotated_df['label'] != -1]
        self.corepoints_centroids = self.corepoints_df.groupby(
            ['label']).mean()


if __name__ == '__main__':
    import sys
    p = RadarPlot()
    timer = QtCore.QTimer()
    timer.timeout.connect(p.update)
    timer.start(100)
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
