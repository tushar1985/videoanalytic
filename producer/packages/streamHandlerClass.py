from packages import detectorAPIstub
from packages.helperFunctions import cameraConfiguration
import cv2
import numpy as np
from copy import deepcopy
import concurrent.futures
import pymongo
class streamHandler:
    def __init__(self,cameraName,cameraPath,detectorAssignments):
        self.cameraPath= cameraPath
        print(f'[StreamHandler-Info] got cameraPath {self.cameraPath}...')
        self.cameraName= cameraName
        self.height=None
        self.width=None
        self.setHeightWidth()
        #detectorAssignments ==>> [('bag', 'http://121.0.0.1:7001/predict'), 
        #example                   ('gun', 'http://46.34.125.111:7500/predict'), 
        #                          ('car', 'http://121.0.0.1:7200/predict')]
        self.detectorAssignments= detectorAssignments
        print('[StreamHandler-Info] VideoStream assigned these detectors: ',self.detectorAssignments)
        #detector functionality
        self.initiateDetectors()
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.videoOutput= cv2.VideoWriter('data/output_'+ self.cameraName +'.avi',fourcc, 10.0, (self.width,self.height)) 
        self.status = True
        #database saving funcitonality
        client= pymongo.MongoClient('mongodb://127.0.0.1:27017')
        db= client['video_analytics']
        self.dbCollection= db[self.cameraName]
        pass
    
    def __del__(self):
        print(f'[Info] Deleting StreamHandler with cameraName: {self.cameraName}')
        print(f'[Info] Closing the video reader and writer if was initiated...')
        self.video.release()
        self.videoOutput.release()
        print(f'[Info] Stream was terminated peacefully...')
        pass
        
    def stop(self):
        self.status=False
        self.video.release()
        self.videoOutput.release()

    def setHeightWidth(self):
        print('[StreamHandler-Info] setting height and width...')
        if self.cameraPath.isdigit():
            self.cameraPath= int(self.cameraPath)
        video = cv2.VideoCapture(self.cameraPath)
        for _ in range(5):
            _, frame = video.read()
            if frame is not None:
                self.height,self.width= frame.shape[:2]
                return True
        video.release()
        raise Exception('CameraRead: videoStream is returning None type frames ')
        pass

    def initiateDetectors(self):
        '''
        detectorGroups= 
        {
            'carDetector': object of detectorAPIstub.detectorClass,
            'bagDetector': object of detectorAPIstub.detectorClass, 
            'hatDetector': object of detectorAPIstub.detectorClass 
        }
        '''
        self.detectorGroups=dict()
        print('[StreamHandler-Info] Initiating detectors...')
        for detectorName, url in self.detectorAssignments:
            self.detectorGroups[detectorName]= detectorAPIstub.objectDetectorClass(detectorName,url,self.height,self.width)
            print(f'[StreamHandler-Info] {detectorName} detector Initiated...')
        pass

    def run(self):
        '''
        capture frame from stream and pass each frame to analyseFrame function
        '''
        self.video = cv2.VideoCapture(self.cameraPath)
        _, frame = self.video.read()
        """ if frame is not None:
            videoWriter = cv2.VideoWriter(filePath, fourCC, 25, (frame.shape[1],frame.shape[0])) """
        self.frameCount=0
        self.status=True
        while True and self.status:
            _, frame = self.video.read()
            if frame is not None:
                self.analyseFrame(frame)
                self.frameCount+=1
            else:
                print(f'[StreamHandler-Info] !!!!!! Received NoneType frame data from camera {self.cameraName} !!!!!!! ')
                break
            self.status= cameraConfiguration(self.cameraName)
            if not self.status:
                self.stop()
                print(f'<<<<<<<<<[Terminating-Info] deleting stream {self.cameraName}>>>>>>>>>')
        pass


    def analyseFrame(self,frame,typee='video'):
        '''
        update detector groups for tracking various bboxes
        '''
        self.frame= frame
        

        frameReport=dict()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            intermediateThreadsDict=dict()
            for detectorName in self.detectorGroups:
                intermediateThreadsDict[executor.submit(self.detectorGroups[detectorName].track, deepcopy(frame))]= detectorName
            for threadObj in concurrent.futures.as_completed(intermediateThreadsDict):
                objectID_with_rects_in_this_frame_dict = threadObj.result()
                frameReport[intermediateThreadsDict[threadObj]] = objectID_with_rects_in_this_frame_dict        
        if typee=='video':
            self.saveReport(frameReport)
        else:
            print(f'[StreamHandler-Info] At this frame we got this report: ',frameReport)
        pass

    def saveReport(self,frameReport):
        print(f'[StreamHandler-Info] {self.cameraName} At frame number {self.frameCount} we got this report: ',frameReport)
        #saving frames to video writer
        self.writeVideo(frameReport)
        #saving to database functionality should be added here
        self.persist(frameReport)
        pass
    
    def writeVideo(self,frameReport):
        self.drawReport(frameReport)
        self.videoOutput.write(self.frame)
        pass

    def drawReport(self,frameReport):
        '''
        {
            'yoloAllObject':{
                                0: {
                                    'position': [312, 355], 
                                    'bbox': [142, 235, 482, 476], 
                                    'time': datetime.datetime(2021, 1, 22, 22, 15, 50, 392146), 
                                    'class': 'person', 
                                    'frameNumber': 32
                                    }
                                    
                            }
        }
        '''
        for detname in frameReport:
            for IDD in frameReport[detname]:
                #gathering info
                idd= IDD
                centroid= tuple(frameReport[detname][IDD]['position'])
                box= tuple(frameReport[detname][IDD]['bbox'])
                x1,y1,x2,y2= max(box[0],0),max(box[1],0),min(box[2],self.width),min(box[3],self.height)
                classname= frameReport[detname][IDD]['class']

                #drawing info (circle point, rectangle, classname,id)
                cv2.rectangle(self.frame, (x1, y1), (x2, y2),(0, 255, 255), 2)
                text = f"ID: {idd}"
                cv2.putText(self.frame, text, ( max((centroid[0] - 10),0), max(0,(centroid[1] - 10)) ),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                cv2.circle(self.frame, centroid, 3, (0, 255, 255), -1)
                #####
                label= str(classname)
                (label_width, label_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                label_patch = np.zeros((label_height + baseline, label_width, 3), np.uint8)
                label_patch[:,:] = (0,255,255)
                labelImage= cv2.putText(label_patch, label, (0, label_height), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)
                label_height,label_width,_= labelImage.shape
                if y1-label_height< 0:
                    y1=label_height
                if x1+label_width> self.width:
                    x1=self.width-label_width
                self.frame[y1-label_height:y1,x1:x1+label_width]= labelImage
        pass

    def persist(self,frameReport):
        '''
        report data:--- 
        {
            'yoloAllObject':{
                                0: {
                                    'position': [312, 355], 
                                    'bbox': [142, 235, 482, 476], 
                                    'time': datetime.datetime(2021, 1, 22, 22, 15, 50, 392146), 
                                    'class': 'person', 
                                    'frameNumber': 32
                                    }
                                    
                            }
        }
        json mongo storage data:---
        post= {'idd':0,'detectorName':'yoloAll','position':[312, 355],'bbox': [142, 235, 482, 476], 
                                    'time': datetime.datetime(2021, 1, 22, 22, 15, 50, 392146), 
                                    'class': 'person', 
                                    'frameNumber': 32 }
        '''
        postList= []
        for detname in frameReport:
            post= dict()
            for IDD in frameReport[detname]:
                post= frameReport[detname][IDD]
                post['idd']=IDD
                post['detectorName']=detname
                postList.append(post)
        if len(postList)>0:
            print('[StreamHandler-Info] Persisting results in db')
            self.dbCollection.insert_many(postList)
        pass


'''------------------------------------------------------------------------------------------------------------------------'''
'''
def analyseFrame(self,frame,typee='video'):
    #update detector groups for tracking various bboxes
    
    self.frame= frame
    frameReport=dict()
    for detectorName in self.detectorGroups:
        objectID_with_rects_in_this_frame_dict= self.detectorGroups[detectorName].track(deepcopy(frame))
        frameReport[detectorName]= objectID_with_rects_in_this_frame_dict
    if typee=='video':
        self.saveReport(frameReport)
    else:
        print(f'[StreamHandler-Info] At this frame we got this report: ',frameReport)
    pass
'''