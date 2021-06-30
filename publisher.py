import zmq
import time
import sys
import pandas as pd
from re import search
from pandaszmq import send_dataframe


def file_slice(file_name):
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


port = "5556"
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)
idx, file_len = file_slice("RadarData\Radar0")
df = pd.read_table("RadarData\Radar0", skiprows=6, skipfooter=file_len -
                   idx-2, delim_whitespace=True, engine='python', header=None)

while True:
    send_dataframe(socket=socket, obj=df)
    time.sleep(1)
