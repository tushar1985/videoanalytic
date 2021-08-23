import cv2
import numpy as np
from flask import Flask, request, Response, send_file, jsonify
from flask_cors import CORS
import traceback
import json
import copy
import pickle
from datetime import datetime
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
CORS(app)

'''============================================================================================================================'''
'''                                    DEFINE INFERENCING MODEL FUNCTIONS HERE'''

'''
Load your model here
model= load(path) etc.............
'''

# define detector function for single image frame
def xyzDetector(frame):
    '''
    code goes here
    '''
    return 

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
	app.run(debug=True,host="0.0.0.0", port=11000)