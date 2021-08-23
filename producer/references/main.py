from packages import streamHandlerClass
from packages.helperFunctions import cameraConfiguration,allCameraConfigurations
import signal
import concurrent.futures
import sys
import os

def die_peacefully(signal, frame):
    print ('You pressed Ctrl+C - or killed me with -2')
    #.... Put your logic here .....
    os._exit(1)

signal.signal(signal.SIGINT, die_peacefully)

class streamBundles:
    def __init__(self):
        self.streamDetails= allCameraConfigurations()
        self.currentStreams=dict()
        self.intermediateThreadsDict=dict()
        for detail in self.streamDetails:
            cameraName,cameraPath,detectorsList=detail
            self.currentStreams[cameraName]= streamHandlerClass.streamHandler(cameraName=cameraName, cameraPath=cameraPath, detectorAssignments= detectorsList)
    
    def newStream(self):
        while True :
            self.streamDetails= allCameraConfigurations()
            cName=[]
            for detail in self.streamDetails:
                cameraName,cameraPath,detectorsList=detail
                if detail[0] not in self.currentStreams.keys():
                    print('[Info] detected changes in config file...')
                    self.currentStreams[cameraName]= streamHandlerClass.streamHandler(cameraName=cameraName, cameraPath=cameraPath, detectorAssignments= detectorsList)
                    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                        self.intermediateThreadsDict[executor.submit(self.currentStreams[cameraName].run)]= cameraName
                cName.append(cameraName)
            delCameras= list(set(self.intermediateThreadsDict.values())-set(cName))
            for cameraName in delCameras:
                print('[info] deleting camera stream')
                self.currentStreams[cameraName].stop()
                self.currentStreams.pop(cameraName)
                for key,val in self.intermediateThreadsDict.items():
                    if val== cameraName:
                        self.intermediateThreadsDict.pop(key)
                    

    def run(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for cameraName in self.currentStreams:
                self.intermediateThreadsDict[executor.submit(self.currentStreams[cameraName].run)]= cameraName
            executor.submit(self.newStream)
            print(f'[Main-Info] started multi streaming...{self.intermediateThreadsDict}')
            

driver= streamBundles()
driver.run()

'''#read details of a specific stream
cameraName,cameraPath,detectorsList= cameraConfiguration(cameraName)
#hire a stream handler object
driver= streamHandlerClass.streamHandler(cameraName=cameraName, cameraPath=cameraPath, detectorAssignments= detectorsList)
driver.run()'''