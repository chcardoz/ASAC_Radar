import zmq
import time
import sys
import pandas as pd
from re import search
from pandaszmq import recv_dataframe


port = "5556"
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://149.162.229.165:%s" % port)

while True:
    data = recv_dataframe(socket=socket)
    print(data)
