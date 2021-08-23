from packages.centroidtracker import CentroidTracker                       #path: '\tracker\pyimagesearch'
from packages.trackableobject import TrackableObject 
import cv2
import numpy as np
from datetime import datetime
import dlib
import time

#path yolov3 model
weights= '/home/dexter/Projects/STY/Retail_Analytics/rhm-server/tracker/models/yolo/yolov3.weights'
configs= '/home/dexter/Projects/STY/Retail_Analytics/rhm-server/tracker/models/yolo/yolo_v3.cfg'

def centroid_in_box(cent, box):
    x1,y1,x2,y2= tuple(box)
    if (cent[0] >= x1 and cent[0] <=x2) and (cent[1] >= y1 and cent[1] <=y2):
        return True
    else:
        return False

def cropPeople(frame,bboxes,headPaddingHeightRatio=1/4):
    #pads the height of the person by given ratio first then creates list of person
    croppedPeople=[]
    for box in bboxes:
        headPadding= int((box[3]-box[1])*headPaddingHeightRatio)
        person= frame[max(0,box[1]-headPadding):box[3],box[0]:box[2]]
        croppedPeople.append(person)
    return croppedPeople


class person_tracker:
    def __init__(self, camID, maxDisappeared=10, maxDistance=50,skipFrames=2,cropFrame=None):                                                                                  
        self.ct = CentroidTracker(maxDisappeared=10, maxDistance=50)              # instantiate our centroid tracker, then initialize a list to store
        self.trackers = []                                                        # each of our dlib correlation trackers, followed by a dictionary to # initialize the list of class labels MobileNet SSD was trained to
        self.trackableObjects = {}
        self.totalFrames= 0
        self.camID= camID
        self.skipFrames= skipFrames
        self.cropFrame= cropFrame
        #for model******
        self.net = cv2.dnn.readNetFromDarknet(configs, weights)
        # determine only the *output* layer names that we need from YOLO
        self.ln = self.net.getLayerNames()
        self.ln = [self.ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]

    def cammeraID(self):
        return self.camID

    def track(self, frame, debug= True):
        debug=True
        (H, W) = frame.shape[:2]
        if self.cropFrame is not None:
            y1,y2,x1,x2= self.cropFrame
            frame= frame[y1:y2,x1:x2,:]
            debug_frame= frame.copy()
        #Frame rate of the  input video
        #in_time = None
        #initialize the frame dimensions
        rects = []

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)#Convert the frame from BGR to RGB for dlib
        debug_frame=frame.copy()
        nmsBBoxes=None
        croppedPeople=None
        BBoxes=[]
        # check to see if we should run a more computationally expensive
        # object detection method to aid our tracker
        if self.totalFrames % self.skipFrames == 0:
            # set the status and initialize our new set of object trackers
            self.trackers = []
            nmsBBoxes, nmsCConfidences, debug_frame= self.yoloPersonDetection(frame.copy(),debug=True)
            croppedPeople= cropPeople(frame.copy(),nmsBBoxes)
            BBoxes=nmsBBoxes
            for box in nmsBBoxes:
                startX,startY,endX,endY= box
                if endX-startX < debug_frame.shape[1]//2: #//////////////////////////////////////////////////////////////////////////////////////////////////////////
                    
                    # construct a dlib rectangle object from the bounding
                    # box coordinates and then start the dlib correlation
                    # tracker
                    tracker = dlib.correlation_tracker()
                    rect = dlib.rectangle(startX,startY,endX,endY)
                    tracker.start_track(rgb, rect)
                    cv2.rectangle(debug_frame, (startX, startY), (endX, endY),
                                    (255, 0, 0), 2)
                    debug_frame = cv2.circle(debug_frame, ((startX+endX)//2,(startY+endY)//2), 3, (0,255,255), -1)
                    self.trackers.append(tracker)
                else:
                    continue
                # add the tracker to our list of trackers so we can
                # utilize it during skip frames
                


        # otherwise, we should utilize our object *trackers* rather than
        # object *detectors* to obtain a higher frame processing throughput
        else:
            # loop over the trackers
            for tracker in self.trackers:
                # set the status of our system to be 'tracking' rather
                # than 'waiting' or 'detecting'
                status = 'Tracking'

                # update the tracker and grab the updated position
                tracker.update(rgb)
                pos = tracker.get_position()
                # unpack the position object
                startX = int(pos.left())
                startY = int(pos.top())
                endX = int(pos.right())
                endY = int(pos.bottom())
                if endX-startX < debug_frame.shape[1]//2: #//////////////////////////////////////////////////////////////////////////////////////////////////////////
                    cv2.rectangle(debug_frame, (startX, startY), (endX, endY),
                                    (255, 0, 0), 2)
                    debug_frame = cv2.circle(debug_frame, ((startX+endX)//2,(startY+endY)//2), 3, (0,255,255), -1)
                    rects.append((startX, startY, endX, endY))
                else:
                    continue
                # add the bounding box coordinates to the rectangles list
                
                #print('rect', rects)
            
            for rect in rects:
                #croppedPeople= cropPeople([startY,endY,startX,endX])
                BBoxes.append(list(rect))
            if len(BBoxes)>0:
                croppedPeople= cropPeople(frame.copy(),BBoxes)

        self.totalFrames += 1
        # use the centroid tracker to associate the (1) old object
        # centroids with (2) the newly computed object centroids
        objects = self.ct.update(rects)
        #attaching id to cropped people in the frame
        person_with_id= dict()
        if croppedPeople is not None:
            for i,bbox in enumerate(BBoxes):
                for (objectID, centroid) in objects.items():
                    if centroid_in_box(centroid, bbox):
                        #print(objectID)
                        x1,y1,x2,y2=tuple(bbox)
                        person_with_id[objectID]= {'pos':((x1+x2)//2,(y1+y2)//2),'time':datetime.now()}
                        cv2.putText(debug_frame, 'ID:'+ str(objectID), ( (x1+x2)//2, max(0,(y1+y2)//2 -5) ), cv2.FONT_HERSHEY_SIMPLEX,
                            0.3, (0,255,255), 1)
                        break

        return (person_with_id, debug_frame)

    def yoloPersonDetection(self, frame,debug=True):
        '''
        sample 720X1280
        *****frame********
        time took in recieving from network 0:00:01.143951
        time took in extracting boxes 0:00:00.037574
        time took in NM supression 0:00:00.000443
        PerFrame Time 0:00:01.182246
        *****frame********
        time took in recieving from network 0:00:04.899312
        time took in extracting boxes 0:00:00.037569
        time took in NM supression 0:00:00.000495
        PerFrame Time 0:00:04.937895
        '''
        H,W,_= frame.shape
        #sending frame to network
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416),swapRB=True, crop=False)
        self.net.setInput(blob)
        layerOutputs = self.net.forward(self.ln)
        #extracting bounding box only for person
        boxxx,boxForNMS, ccconfidences= self.getBBoxes(layerOutputs,W,H)
        
        #receiving bounding boxes after non-maximum-supression
        nmsBBoxes,nmsCConfidences,debug_frame= self.nmsBBoxes(frame, boxxx, boxForNMS, ccconfidences, \
                                        confThresh=0.6, thresh=0.3,debug=debug)
        
        if debug ==True:
            return nmsBBoxes,nmsCConfidences,debug_frame
        else:
            return nmsBBoxes,nmsCConfidences,None

    def nmsBBoxes(self,frame, boxes, boxForNMS, confidences, confThresh=0.6, thresh=0.3,debug=True):
        idxs = cv2.dnn.NMSBoxes(boxForNMS, confidences, confThresh, thresh)
        # ensure at least one detection exists
        nmsBBoxes=[]
        nmsCConfidences=[]
        if len(idxs) > 0:
            # loop over the indexes we are keeping
            for i in idxs.flatten():
                x,y,x2,y2 = boxes[i]
                if x2-x < frame.shape[1]//2: #//////////////////////////////////////////////////////////////////////////////////////////////////////////
                    # extract the bounding box coordinates
                    #(x, y) = (boxes[i][0], boxes[i][1])
                    nmsBBoxes.append([x,y,x2,y2])
                    nmsCConfidences.append(confidences[i])
                    #(w, h) = (boxes[i][2], boxes[i][3])
                    # draw a bounding box rectangle and label on the image
                    #color = [int(c) for c in COLORS[classIDs[i]]]
                
                    cv2.rectangle(frame, (x, y), (x2,y2), (255,0,0), 2)
                    text = "{}: {:.4f}".format('person', confidences[i])
                    cv2.putText(frame, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                        0.3, (0,255,0), 1)
                else:
                    continue
                
        if debug==True:
            return nmsBBoxes, nmsCConfidences, frame
        else:
            return nmsBBoxes, nmsCConfidences, None

    def getBBoxes(self,layerOutputs,W,H):
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
        for i,predClass in enumerate(classIDs):
            if predClass == 0:
                x1,y1,w,h= boxes[i]
                #converting boundb format from x,y,w,h to x1,y1,x2,y2
                boxxx.append([int(x1),int(y1),int(x1+w),int(y1+h)])
                boxForNMS.append(boxes[i])
                ccconfidences.append(confidences[i])
        return boxxx,boxForNMS,ccconfidences

