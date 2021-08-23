from packages.helperFunctions import cameraConfiguration,allCameraConfigurations,configureDB, rabbitCheck
from configurations.backendConfig import conf as backendConfigurations

import signal
import pika
import concurrent.futures
import sys
import traceback
import os
import cv2
import traceback


def die_peacefully(signal, frame):
    print ('You pressed Ctrl+C - or killed me with -2')
    #.... Put your logic here .....
    os._exit(1)

signal.signal(signal.SIGINT, die_peacefully)
configureDB()
rabbitCheck()

#connect with rmq server
#monitor config file all the time for getting any changes
#start or stop particular stream onto rmq at runtime as per config file changes
#publishes each stream to different queue which are created and subscribed at runtime
#all seperate streaming processes are concurrent and parallel
class rmqStreamProducer:
    def __init__(self):
        #rabbitmq credentials
        print("[Prod Info] Intialization started!")
        self.RMQusername= backendConfigurations['test']
        self.RMQpassword= backendConfigurations['test']
        self.RMQhost= backendConfigurations['localhost']
        print(f"[Prod Info] Pointing to RabbitMQ server at {self.RMQhost}:15672 ")
        print(f"[Prod Info] Pointing to MongoDB server at {backendConfigurations['mongo:latest:27017']}")
        self.RMQexchangeType= backendConfigurations['RMQexchangeType']
        #reading camera configurations
        self.streamDetails= allCameraConfigurations()
        self.currentStreams=dict()
        for detail in self.streamDetails:
            cameraName,cameraPath,detectorsList=detail
            self.currentStreams[cameraName]= cameraPath
        #establishing connection
        self.enableConnection()
        self.declareQueues()
        print("[Prod Info] Intialization Done!")
        print("[Prod Info] Monitoring Camera Config Entries!")

    def enableConnection(self):
        credentials = pika.PlainCredentials(self.RMQusername,self.RMQpassword)
        self.connection= pika.BlockingConnection(pika.ConnectionParameters(host=self.RMQhost, credentials= credentials))
        self.channelDict= dict()
        for cameraName in self.currentStreams:
            self.channelDict[cameraName]= self.connection.channel()
            self.channelDict[cameraName].exchange_declare(cameraName, durable=True, exchange_type=self.RMQexchangeType)

    def reConnect(self,cameraName):
        credentials = pika.PlainCredentials(self.RMQusername,self.RMQpassword)
        self.connection= pika.BlockingConnection(pika.ConnectionParameters(host=self.RMQhost, credentials= credentials))
        self.channelDict[cameraName]= self.connection.channel()
        self.channelDict[cameraName].exchange_declare(cameraName, durable=True, exchange_type=self.RMQexchangeType)
        
    def declareQueues(self,camName=False):
        if camName !=  False:
            self.channelDict[camName].queue_declare(queue= camName)
            self.channelDict[camName].queue_bind(exchange=camName, queue=camName, routing_key=camName)
            return True
        for cameraName in self.currentStreams:
            self.channelDict[cameraName].queue_declare(queue= cameraName)
            self.channelDict[cameraName].queue_bind(exchange=cameraName, queue=cameraName, routing_key=cameraName)

    def delQueue(self, name):
        credentials = pika.PlainCredentials(self.RMQusername,self.RMQpassword)
        connection= pika.BlockingConnection(pika.ConnectionParameters(host=self.RMQhost, credentials= credentials))
        channel=connection.channel()
        channel.queue_delete(name)
        print(f'[Producer Info] deleted queue {name} ************')

    def readAndPublish(self,cameraPath,cameraName):
        # this function can be called from different threads
        # reads the feed from the camera path and publish each frame to the particular queue
        # at each iteration checks whether to continue the streaming or to stop it by monitoring config file
        video = cv2.VideoCapture(cameraPath)
        status=True
        flip=True
        while True and status:
            _, frame = video.read()
            if flip:
                flip=False
                continue
            try:
                status= cameraConfiguration(cameraName)
                if not status:
                    print(f'<<<<<<<<<[Terminating-Info] deleting stream {cameraName}>>>>>>>>>')
                    break
                if frame is not None:
                    _, img_encoded = cv2.imencode('.jpg', frame)
                    #while self.channelDict[cameraName].is
                    #print(dir(self.connection),self.connection.is_open)
                    while not (self.connection.is_open and self.channelDict[cameraName].is_open):
                        self.reConnect(cameraName)
                        print(f'[Producer Info] establised RMQ connection with {cameraName}',self.connection.is_open,self.channelDict[cameraName].is_open)
                    self.channelDict[cameraName].basic_publish(exchange=cameraName,
                                                properties=pika.BasicProperties( headers={'cameraName': cameraName} ),
                                                routing_key=cameraName,
                                                body= img_encoded.tostring())
                else:
                    print(f'[VideoReader-Info] !!!!!! Received NoneType frame data from camera {cameraName} !!!!!!! ')
                    break
            except Exception as e:
                print(e,'*'*50)
                traceback.print_exc()
        pass
    
    def run(self):
        # executing readAndPublish function in multithreaded env for each stream with dynamic monitoring of config file
        with concurrent.futures.ThreadPoolExecutor(max_workers=backendConfigurations['maxThreadWorkers']) as executor:
            #start the current available stream details in configuration file in different threads
            self.threadList=dict()
            for cameraName,cameraPath in self.currentStreams.items():
                self.threadList[cameraName]=executor.submit(self.readAndPublish,cameraPath,cameraName)
            #after first start we will run monitoring to check the config file changes and start or stop particular thread accordingly
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
                        self.delQueue(cameraName)
                    #adding new streams which are read from confuguration file
                    addCameras= list(set(cName)- set(self.currentStreams.keys() ))
                    for detail in self.streamDetails:
                        cameraName,cameraPath,detectorsList=detail
                        if cameraName in addCameras:
                            print(f'[Change Info] detected changes in config file {cameraName}...')
                            #start the current available stream details in confuguration file in different threads
                            self.currentStreams[cameraName]=cameraPath
                            self.reConnect(cameraName)
                            self.declareQueues(cameraName)
                            self.threadList[cameraName]=  executor.submit(self.readAndPublish,cameraPath,cameraName) 
                
                except Exception as e:
                    print('===',e)
                    traceback.print_exc() 


prod= rmqStreamProducer()
prod.run()