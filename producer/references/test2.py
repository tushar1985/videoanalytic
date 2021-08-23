import cv2
import numpy as np
from datetime import datetime
import dlib
import time
import json
from PIL import Image
from six import StringIO
import requests
from configparser import ConfigParser
#import threading
#apiURL= 'http://54.164.68.250:11000/predict'
#apiURL= 'http://0.0.0.0:11000/predict'
def apiCall(frame):
    nmsBBox = None
    _, img_encoded = cv2.imencode('.jpg', frame) 
    response = requests.post(
        url=apiURL,
        data=img_encoded.tobytes()
    )
    print('got data','*'*10)
    data= json.loads(response.text)
    print(data)
#frame= cv2.imread('immm.jpg')
#print(frame.shape)
#time= datetime.now()
#apiCall(frame)
#print(datetime.now()-time)
import concurrent.futures
import signal
import sys
def funn():
    time.sleep(5)
    print('done')
'''
with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
   executor.submit(funn)
   executor.submit(funn)
'''
executor= concurrent.futures.ThreadPoolExecutor(max_workers = 5)  
executor.submit(funn)
executor.submit(funn)
print('hello')
