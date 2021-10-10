import zmq
import time
import sys
import pandas as pd
from re import search
from pandaszmq import recv_dataframe


port = "9090"
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:%s" % port)
socket.subscribe("")


while True:
    df = recv_dataframe(socket=socket)
    print(df)
