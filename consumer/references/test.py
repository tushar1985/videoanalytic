import cv2
import numpy as np
from datetime import datetime
import dlib
import time
import json
from PIL import Image
from six import StringIO
import requests
apiURL= "http://54.164.68.250:11000/predict"

def apiCall(frame):
    nmsBBox = None
    _, img_encoded = cv2.imencode('.jpg', frame) 
    response = requests.post(
        url=apiURL,
        data=img_encoded.tostring()
    )
    data= json.loads(response.content)
    print(data)

cap = cv2.VideoCapture('http://192.168.0.102:8080/video')
# Capture frame-by-frame
ret, frame = cap.read()
fps = cap.get(cv2.CAP_PROP_FPS)
print(fps,frame.shape)
iterr=0
while(True):
    
    # Capture frame-by-frame
    ret, frame = cap.read()
    if ret==True:
        if iterr%55==0 :
            time= datetime.now()
            apiCall(frame)
            print(datetime.now()-time)
    else:
        break
    iterr+=1

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()