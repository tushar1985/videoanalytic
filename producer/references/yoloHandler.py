import copy
import pickle
from datetime import datetime
import cv2
import numpy as np
import matplotlib.pyplot as plt
def show(frame):
    plt.figure(figsize=(20,100))
    plt.imshow(frame)


class yoloIzer:
    def __init__(self,configsPath,weightsPath,detectAll=False,classes=['person']):
        self.classes= ['person', 'bicycle', 'car', 'motorbike', 'aeroplane', 'bus', 'train', 'truck', 'boat', \
        'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog',\
         'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',\
          'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', \
          'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', \
          'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', \
          'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'sofa', 'pottedplant', 'bed',\
           'diningtable', 'toilet', 'tvmonitor', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',\
            'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', \
            'teddy bear', 'hair drier', 'toothbrush']
        self.classesDict={}
        for i,name in enumerate(self.classes):
            self.classesDict[i]=name
        self.configsPath=configsPath
        self.weightsPath=weightsPath
        self.classes= classes
        self.net = cv2.dnn.readNetFromDarknet(configsPath, weightsPath)
        ln = self.net.getLayerNames()
        self.ln = [ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
    
    def infer(self,frame):
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416),swapRB=True, crop=True)
        H,W,_= frame.shape
        self.net.setInput(blob)
        layerOutputs = self.net.forward(self.ln)
        boxxx,boxForNMS, ccconfidences,cName= self.getBBoxes(layerOutputs,W,H)
        nmsBBoxes,nmsCConfidences,debug_frame,cName= self.getNmsBboxes(copy.deepcopy(frame), boxxx, boxForNMS,cName\
                                ,ccconfidences,confThresh=0.6, thresh=0.3,debug=True)
        return nmsBBoxes,nmsCConfidences,debug_frame,cName
    
    def getNmsBboxes(self, frame, boxes, boxForNMS,cName, confidences, confThresh=0.6, thresh=0.3,debug=True):
        idxs = cv2.dnn.NMSBoxes(boxForNMS, confidences, confThresh, thresh)
        # ensure at least one detection exists
        nmsBBoxes=[]
        nmsCConfidences=[]
        namess=[]
        if len(idxs) > 0:
            # loop over the indexes we are keeping
            for i in idxs.flatten():
                # extract the bounding box coordinates
                #(x, y) = (boxes[i][0], boxes[i][1])
                x,y,x2,y2 = boxes[i]
                nmsBBoxes.append([x,y,x2,y2])
                nmsCConfidences.append(confidences[i])
                namess.append(cName[i])
                #(w, h) = (boxes[i][2], boxes[i][3])
                # draw a bounding box rectangle and label on the image
                #color = [int(c) for c in COLORS[classIDs[i]]]
                cv2.rectangle(frame, (x, y), (x2,y2), (255,0,0), 2)
                text = "{}: {:.4f}".format(cName[i], confidences[i])
                cv2.putText(frame, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                    0.3, (0,255,0), 1)
        if debug==True:
            return nmsBBoxes, nmsCConfidences, frame , namess
        else:
            return nmsBBoxes, nmsCConfidences, None, namess
        
    def getBBoxes(self, layerOutputs,W,H):
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
            if self.classesDict[predClass] in self.classes:
                x1,y1,w,h= boxes[i]
                #converting boundb format from x,y,w,h to x1,y1,x2,y2
                boxxx.append([int(x1),int(y1),int(x1+w),int(y1+h)])
                boxForNMS.append(boxes[i])
                ccconfidences.append(confidences[i])
                cName.append(self.classesDict[predClass])
        return boxxx,boxForNMS,ccconfidences,cName
