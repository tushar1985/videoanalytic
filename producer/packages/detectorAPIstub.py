from packages.centroidtracker import CentroidTracker                       #path: '\tracker\pyimagesearch'
from packages.trackableobject import TrackableObject 
import cv2
import numpy as np
from datetime import datetime
import dlib
import time
import json
from PIL import Image
from six import StringIO
import requests



class objectDetectorClass:
    def __init__(self, detectorName, url, height, width, maxDisappeared=10, maxDistance=50,skipFrames=2):                                                                                  
        self.ct = CentroidTracker(maxDisappeared=10, maxDistance=50)# instantiate our centroid tracker, then initialize a list to store
        self.trackers = [] # each of our dlib correlation trackers, followed by a dictionary to # initialize the list of class labels MobileNet SSD was trained to
        self.trackableObjects = {}
        self.totalFrames= 0
        self.apiURL= url
        self.detectorName=detectorName
        self.skipFrames= skipFrames
        self.height= height
        self.width= width
        #for API****
        self.testAPILiveliness()

    def testAPILiveliness(self):
        resp= requests.post(self.apiURL+'/ping').text
        if resp == 'ready':
            print(f'    [Detector-Info] {self.detectorName} API endpoint is live! ')
        else:
            print(f'    [Detector-Info] {self.detectorName} API endpoint is inactive! ')
            raise Exception(f' APILiveliness: API endpoint with url: {self.apiURL} is inactive! ')

    def details(self):
        det={'name':self.detectorName,'apiURL':self.apiURL}
        print(det)
        return det

    def centroid_in_box(self, cent, box):
        x1,y1,x2,y2= tuple(box)
        if (cent[0] >= x1 and cent[0] <=x2) and (cent[1] >= y1 and cent[1] <=y2):
            return True
        else:
            return False

    def apiCall(self,frame):
        _, img_encoded = cv2.imencode('.jpg', frame) 
        print(f'    [Detector-Info] calling {self.detectorName} api...')
        response = requests.post(
            url=self.apiURL,
            data=img_encoded.tobytes()
        )
        print(f'    [Detector-Info] {self.detectorName} gave Response {response.status_code}...')
        data= json.loads(response.text)
        return (data['bbox'],data['cname'])
        

    def track(self, frame, debug= True):
        '''
        1. At Every skipframe, API inference
        2. At Else frame, correlation tracker for faster throughput
        3. Update the bounding boxes in centroid tracker
        4. Return dictionary of obj Id, position, bbox, timestamp, class name, frameNumber 
        '''
        time=datetime.now()
        rects = []
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)#Convert the frame from BGR to RGB for dlib
        nmsBBoxes=None
        BBoxes=[]
        # check to see if we should run a more computationally expensive
        # object detection method to aid our tracker
        if self.totalFrames % self.skipFrames == 0:

            self.trackers = []
            nmsBBoxes,self.cname= self.apiCall(frame)
            BBoxes=nmsBBoxes
            for box in nmsBBoxes:
                startX,startY,endX,endY= box
                # construct a dlib rectangle object from the bounding
                # box coordinates and then start the dlib correlation
                tracker = dlib.correlation_tracker()
                rect = dlib.rectangle(startX,startY,endX,endY)
                tracker.start_track(rgb, rect)
                self.trackers.append(tracker)

        # otherwise, we should utilize our object *trackers* rather than
        # object *detectors* to obtain a higher frame processing throughput
        else:
            # loop over the trackers
            for tracker in self.trackers:
                # update the tracker and grab the updated position
                tracker.update(rgb)
                pos = tracker.get_position()
                # unpack the position object
                startX = int(pos.left())
                startY = int(pos.top())
                endX = int(pos.right())
                endY = int(pos.bottom())
                rect= (startX, startY, endX, endY)
                rects.append(rect)
                # add the bounding box coordinates to the rectangles list
                BBoxes.append(list(rect))

        # use the centroid tracker to associate the (1) old object
        # centroids with (2) the newly computed object centroids
        objects = self.ct.update(rects)
        #attaching id to cropped people in the frame
        object_with_id= dict()
        for i,bbox in enumerate(BBoxes):
            for (objectID, centroid) in objects.items():
                if self.centroid_in_box(centroid, bbox):
                    x1,y1,x2,y2=tuple(bbox)
                    object_with_id[objectID]= {'position':[(x1+x2)//2,(y1+y2)//2], 'bbox':list(bbox), 'time':time,'class':self.cname[i],'frameNumber':self.totalFrames}
                    break

        self.totalFrames += 1
        return object_with_id