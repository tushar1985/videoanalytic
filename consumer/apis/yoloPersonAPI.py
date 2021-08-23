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
'''--------------------------------------------YOLO INFERENCING MODEL FUNCTIONS--------------------------------------------'''

configs='yolo_v3.cfg'
weights= 'yolov3.weights'

classes= ['person', 'bicycle', 'car', 'motorbike', 'aeroplane', 'bus', 'train', 'truck', 'boat', \
        'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog',\
         'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',\
          'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', \
          'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', \
          'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', \
          'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'sofa', 'pottedplant', 'bed',\
           'diningtable', 'toilet', 'tvmonitor', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',\
            'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', \
            'teddy bear', 'hair drier', 'toothbrush']
classesDict={}
for i,name in enumerate(classes):
    classesDict[i]=name
class getNet:
    def __init__(self):
        self.net= cv2.dnn.readNetFromDarknet(configs, weights)
        self.ln = self.net.getLayerNames()
        self.ln = [self.ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
    def get(self):
        return self.net, self.ln

'''
net = cv2.dnn.readNetFromDarknet(configs, weights)
# determine only the *output* layer names that we need from YOLO
ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]
'''
#netClass = getNet()

def yoloPersonDetection(frame,debug=True,detectAll=False,classess=['person']):
    global classes, netClass
    if not detectAll:
        classes =classess

    H,W,_= frame.shape
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416),swapRB=True, crop=False)
    netClass = getNet()
    net,ln= netClass.get()
    net.setInput(blob)
    layerOutputs = net.forward(ln)
    boxxx,boxForNMS, ccconfidences, cname= getBBoxes(layerOutputs,W,H)
    nmsBBoxes,nmsCConfidences,cname= getnmsBBoxes(frame, boxxx, boxForNMS, ccconfidences, \
                                    cname,confThresh=0.6, thresh=0.3,debug=debug)
    
    return nmsBBoxes,nmsCConfidences,cname

def getnmsBBoxes(frame, boxes, boxForNMS, confidences, cName,confThresh=0.6, thresh=0.3,debug=True):
    idxs = cv2.dnn.NMSBoxes(boxForNMS, confidences, confThresh, thresh)
    # ensure at least one detection exists
    nmsBBoxes=[]
    nmsCConfidences=[]
    namess=[]
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            x,y,x2,y2 = boxes[i]
            # extract the bounding box coordinates
            nmsBBoxes.append([x,y,x2,y2])
            nmsCConfidences.append(confidences[i])
            namess.append(cName[i])

    return nmsBBoxes, nmsCConfidences, namess


def getBBoxes(layerOutputs,W,H):
    global classesDict,classes
    #Extracting bounding boxes from layerOutputs
    boxes = []
    confidences = []
    classIDs = []
    for output in layerOutputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability) of
            # the current object detection
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]
            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > 0.6:
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")
                # use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))
                # update our list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)
    # Filtering for person
    boxxx=[]
    boxForNMS=[]
    ccconfidences=[]
    cName=[]
    for i,predClass in enumerate(classIDs):
        #if predClass == 0:
        if classesDict[predClass] in classes:
            x1,y1,w,h= boxes[i]
            #converting boundb format from x,y,w,h to x1,y1,x2,y2
            boxxx.append([int(x1),int(y1),int(x1+w),int(y1+h)])
            boxForNMS.append(boxes[i])
            ccconfidences.append(confidences[i])
            cName.append(classesDict[predClass])
    return boxxx,boxForNMS,ccconfidences,cName

'''============================================================================================================================'''


def detect(frame):
    ### Call your detector here, Then return the output in same format as defined in example
    ### Write your code below vvvvvvvvvvv
    nmsBBoxes, nmsCConfidences,cname= yoloPersonDetection(frame,detectAll=True,classess=['person'],debug=True)
    ### Write your code above ^^^^^^^^^^^
    '''
    ###Below should not be changed====================
    format of:-
        list_of_bounding_boxes= [[x1,y1,x2,y2],[x1,y1,x2,y2],[x1,y1,x2,y2]]
        list_of_classes_corresponding_to_boundingBoxes= ['person','car','person']
    '''
    list_of_bounding_boxes= nmsBBoxes
    list_of_classes_corresponding_to_boundingBoxes= cname
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
    debug_frame=frame.copy()
    cv2.imwrite('frame.jpg',frame)
    bboxes,boxesClasses= detect(frame)
    data= {'bbox':bboxes,'cname':boxesClasses}
    return json.dumps(data)

if __name__ == '__main__':
	app.run(debug=True,host="0.0.0.0", port=11000)