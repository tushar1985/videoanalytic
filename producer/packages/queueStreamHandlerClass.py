from packages import detectorAPIstub
from packages.helperFunctions import cameraConfiguration, additionalMap
from configurations import backendConfig
import cv2
import numpy as np
from copy import deepcopy
import concurrent.futures
import pymongo
import requests
import json
class streamHandler:
    def __init__(self,cameraName,cameraPath,detectorAssignments):
        self.cameraPath= cameraPath
        print(f'[StreamHandler-Info] got cameraPath {self.cameraPath}...')
        self.cameraName= cameraName
        self.height=None
        self.width=None
        self.frameCount=0
        self.status= True
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
        # client= pymongo.MongoClient(backendConfig.conf['mongoLink'])
        # db= client['video_analytics']
        # self.dbCollection= db[self.cameraName]
        pass
    
    def __del__(self):
        print(f'[Info] Deleting StreamHandler with cameraName: {self.cameraName}')
        print(f'[Info] Closing the video reader and writer if was initiated...')
        self.videoOutput.release()
        print(f'[Info] Stream was terminated peacefully...')
        pass
        
    def stop(self):
        self.status=False
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

    def run(self,frame):
        '''
        capture frame from stream and pass each frame to analyseFrame function
        '''
        
        config= cameraConfiguration(self.cameraName)
        print(config)
        if config== False:
            self.status= False
        else:
            self.status= True
        if (frame is not None) and self.status:
            self.analyseFrame(frame)
            self.frameCount+=1
        else:
            print(f'[StreamHandler-Info] !!!!!! Received NoneType frame data from camera {self.cameraName} !!!!!!! ')
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor3:
            intermediateThreadsDict=dict()
            for detectorName in self.detectorGroups:
                intermediateThreadsDict[executor3.submit(self.detectorGroups[detectorName].track, deepcopy(frame))]= detectorName
            for threadObj in concurrent.futures.as_completed(intermediateThreadsDict):
                objectID_with_rects_in_this_frame_dict = threadObj.result()
                frameReport[intermediateThreadsDict[threadObj]] = objectID_with_rects_in_this_frame_dict     

        if backendConfig.conf['getAdditionalReport']:
            additonalAlgoDict= additionalMap()           
            for detectorName in self.detectorGroups:
                if detectorName in additonalAlgoDict.keys():
                    algoUrl= additonalAlgoDict[detectorName][1]
                    frameReport= self.grabAdditionalReport(detectorName,frameReport,algoUrl)

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
        try:
            postList= []
            for detname in frameReport:
                post= dict()
                for IDD in frameReport[detname]:
                    post= frameReport[detname][IDD]
                    post['idd']=IDD
                    post['detectorName']=detname
                    postList.append(post)
            if len(postList)>0:
                print('[StreamHandler-Info] Persisting results in db', postList)
                with pymongo.MongoClient(backendConfig.conf['mongoLink']) as client:
                    db= client['video_analytics']
                    dbCollection= db[self.cameraName]
                    dbCollection.insert_many(postList)
        except Exception as e:
            print(e,'@@@@persist')
        pass

    def hitTheUrlForReport(self,image,urll):
        _, img_encoded = cv2.imencode('.jpg', image) 
        print(f'[StreamHandler-Info] requesting advanced api {urll}')
        resp= requests.post(urll,data= img_encoded.tobytes())
        report=json.loads(resp.text)   
        return report

    def grabAdditionalReport(self,detectorName,frameReport,algoUrl):
        '''
        report data:--- 
        {
            'yoloAllObject':{
                                0: {
                                    'position': [312, 355], 
                                    'bbox': [142, 235, 482, 476], 
                                    'time': datetime.datetime(2021, 1, 22, 22, 15, 50, 392146), 
                                    'class': 'person', <<===== This is where we will add the additional report
                                    'frameNumber': 32
                                    }
                                    
                            }
        }
        * grabs the detectorName and extract frameReport
            -with this we crop the image for the targeted object with its id
            -then hit the algourl with the cropped image and get the json dictionary as report
            -now that we have the additional report we then add it to the frameReport at the place of class 
        '''
        try:
            objectImages,bboxes,idds= [],[],[]
            objDict= frameReport[detectorName]
            for idd,val in objDict.items():
                x1,y1,x2,y2= val['bbox']
                obj=self.frame[y1:y2,x1:x2]
                objectImages.append(obj)
                bboxes.append(val['bbox'])
                idds.append(idd)

            objReport=dict()
            with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor2:
                intermediateThreadsDict=dict()
                i=0
                for obj in objectImages:
                    intermediateThreadsDict[executor2.submit(self.hitTheUrlForReport, obj, algoUrl)]= f'{detectorName}{i}'
                    i+=1
                for threadObj in concurrent.futures.as_completed(intermediateThreadsDict):
                    objectID_with_rects_in_this_frame_dict = threadObj.result()
                    objReport[intermediateThreadsDict[threadObj]] = objectID_with_rects_in_this_frame_dict 

            objDetails=[]
            for i in range(len(objReport.keys())):
                objDetails.append(objReport[f'{detectorName}{i}'])

            i=0
            for idd in idds:
                frameReport[detectorName][idd]['class']=objDetails[i]
                i+=1
            return frameReport    
        except Exception as e:
            print(e, '@@@@grabAdditionalReport')