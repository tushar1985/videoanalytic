import cv2
import numpy as np
from flask import Flask, request, Response, send_file, jsonify
import traceback
import json
import copy
import pickle
from datetime import datetime
import matplotlib.pyplot as plt
import os
from mtcnn import MTCNN #0.1.0

app = Flask(__name__)

'''============================================================================================================================'''
'''                                    DEFINE INFERENCING MODEL FUNCTIONS HERE'''
def initialize_detector():
	global face_detector
	face_detector = MTCNN()
initialize_detector()

# define detector function for single image frame
def xyzDetector(frame):
    global face_detector
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    detections = face_detector.detect_faces(img_rgb)
    confBBoxes=[([detection['box'][0],detection['box'][1],detection['box'][2]+detection['box'][0],detection['box'][3]+detection['box'][1]],detection['confidence']) for detection in detections]
    return [box for box,conf in confBBoxes],['face' for _ in range(len(confBBoxes))]

'''============================================================================================================================'''


def detect(frame):
    '''Call your detector here, Then return the output in same format as defined in example
        Write your code below vvvvvvvvvvv '''
    BBoxes,classNames= xyzDetector(frame)
    ### 
    ''' Write your code above ^^^^^^^^^^^
    ###Below should not be changed====================
    format of:-
        list_of_bounding_boxes= [[x1,y1,x2,y2],[x1,y1,x2,y2],[x1,y1,x2,y2]]
        list_of_classes_corresponding_to_boundingBoxes= ['person','car','person']
    '''
    list_of_bounding_boxes= BBoxes
    list_of_classes_corresponding_to_boundingBoxes= classNames
    return list_of_bounding_boxes , list_of_classes_corresponding_to_boundingBoxes

def getImage(r):
    # convert string of image data to uint8
    nparr = np.frombuffer(r.data, np.uint8)
    # decode image
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return image


@app.route("/predict/ping", methods=['POST','GET'])
def ping():
	return str('ready')

@app.route("/predict", methods=['POST','GET'])
def main():
    frame= getImage(request)
    cv2.imwrite('frame.jpg',frame)
    bboxes,boxesClasses= detect(frame)
    data= {'bbox':bboxes,'cname':boxesClasses}
    return json.dumps(data)

if __name__ == '__main__':
	app.run(debug=True,host="0.0.0.0", port=12000)