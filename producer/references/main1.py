from packages import streamHandlerClass
from packages.helperFunctions import cameraConfiguration,allCameraConfigurations
import signal
import concurrent.futures
import sys
import traceback
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

    def run(self):
        '''
        members in focus:
            self.intermediateThreadsDict
            self.currentStreams
        '''
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            #start the current available stream details in confuguration file in different threads
            threadList=dict()
            for cameraName in self.currentStreams:
                threadList[cameraName]=executor.submit(self.currentStreams[cameraName].run)
            #manage the addition and deletion of new streams added during runtime
        while True :
            try:
                #reading the coniguration file at runtime
                self.streamDetails= allCameraConfigurations()
                cName=[]
                for detail in self.streamDetails:
                    cameraName,cameraPath,detectorsList=detail
                    cName.append(cameraName)
                #remove older streams which are not now in confuguration file
                delCameras=list(set(self.currentStreams.keys())-set(cName))
                for cameraName in delCameras:
                    self.currentStreams.pop(cameraName)
                #adding new streams which are read from confuguration file
                addCameras= list(set(cName)- set(self.currentStreams.keys() ))
                for detail in self.streamDetails:
                    cameraName,cameraPath,detectorsList=detail
                    if cameraName in addCameras:
                        print('[Info] detected changes in config file...')
                        self.currentStreams[cameraName]= streamHandlerClass.streamHandler(cameraName=cameraName, cameraPath=cameraPath, detectorAssignments= detectorsList)
                        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                            executor.submit(self.currentStreams[cameraName].run) 
            
            except Exception as e:
                print('===',e)
                traceback.print_exc() 

        print(f'[Main-Info] started multi streaming...{self.intermediateThreadsDict}')
            

driver= streamBundles()
driver.run()

'''#read details of a specific stream
cameraName,cameraPath,detectorsList= cameraConfiguration(cameraName)
#hire a stream handler object
driver= streamHandlerClass.streamHandler(cameraName=cameraName, cameraPath=cameraPath, detectorAssignments= detectorsList)
driver.run()'''