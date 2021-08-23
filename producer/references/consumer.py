from packages import queueStreamHandlerClass as streamHandlerClass
from packages.helperFunctions import cameraConfiguration,allCameraConfigurations
from configurations.backendConfig import conf as backendConfigurations

import signal
import concurrent.futures
import sys
import traceback
import os
import numpy as np
import cv2 
import pika 
'''
setting the auto ack parameter false helped to manualy ack the server
for the queued data otherwise it was getting lost during server connection loss period
'''

def die_peacefully(signal, frame):
    print ('You pressed Ctrl+C - or killed me with -2')
    #.... Put your logic here .....
    os._exit(1)

signal.signal(signal.SIGINT, die_peacefully)

#similar to producer it monitors config file and consumes in multithreaded format
#consumer has a callback function which runs our main 
class rmqStreamConsumer:
    def __init__(self):
        self.RMQusername= backendConfigurations['RMQusername']
        self.RMQpassword= backendConfigurations['RMQpassword']
        self.RMQhost= backendConfigurations['RMQhost']
        self.RMQexchangeType= backendConfigurations['RMQexchangeType']
        self.currentStreams=dict()
        self.streamDetails= allCameraConfigurations()
        for detail in self.streamDetails:
            cameraName,cameraPath,detectorsList=detail
            self.currentStreams[cameraName]= streamHandlerClass.streamHandler(cameraName=cameraName, cameraPath=cameraPath, detectorAssignments= detectorsList)                 


    def callbackFunctionForQueues(self,ch,method,properties,body):
        try:
            buff = np.fromstring(body, np.uint8)
            buff = buff.reshape(1, -1)
            frame = cv2.imdecode(buff, cv2.IMREAD_COLOR)
            cameraName= properties.headers['cameraName']
            self.currentStreams[cameraName].run(frame)
        except :
            pass
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def startConsuming(self,cameraName):
        while True:
            try:
                credentials = pika.PlainCredentials(self.RMQusername,self.RMQpassword)
                connection= pika.BlockingConnection(pika.ConnectionParameters(host=self.RMQhost, credentials= credentials))
                channel= connection.channel()
                channel.exchange_declare(cameraName, durable=True, exchange_type=self.RMQexchangeType)
                channel.queue_declare(queue= cameraName)
                channel.queue_bind(exchange=cameraName, queue=cameraName, routing_key=cameraName)
                channel.basic_consume(queue=cameraName,  on_message_callback=self.callbackFunctionForQueues, auto_ack=False)
                channel.start_consuming()
            except:
                continue

    def run(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=backendConfigurations['maxThreadWorkers']) as executor:
            self.threadList=dict()
            for cameraName in self.currentStreams:
                self.threadList[cameraName]=executor.submit(self.startConsuming,cameraName)
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
                        self.threadList.pop(cameraName)
                    #adding new streams which are read from confuguration file
                    addCameras= list(set(cName)- set(self.currentStreams.keys() ))
                    for detail in self.streamDetails:
                        cameraName,cameraPath,detectorsList=detail
                        if cameraName in addCameras:
                            print(f'[Change Info] detected changes in config file {cameraName}...')
                            #start the current available stream details in confuguration file in different threads
                            self.currentStreams[cameraName]= streamHandlerClass.streamHandler(cameraName=cameraName, cameraPath=cameraPath, detectorAssignments= detectorsList) 
                            self.threadList[cameraName]=  executor.submit(self.startConsuming,cameraName) 
                
                except Exception as e:
                    print('===',e)
                    traceback.print_exc() 

cons= rmqStreamConsumer()
cons.run()