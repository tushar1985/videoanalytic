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

def callbackFunctionForQueues(ch,method,properties,body):
    print(body)

RMQusername= 'test'
RMQpassword= 'test'
RMQhost= 'localhost'
RMQexchangeType= 'topic'

credentials = pika.PlainCredentials(RMQusername,RMQpassword)
connection= pika.BlockingConnection(pika.ConnectionParameters(host=RMQhost, credentials= credentials))
channel= connection.channel()

cameraName= 'hello'
channel.basic_consume(queue=cameraName,  on_message_callback=callbackFunctionForQueues, auto_ack=False)
channel.start_consuming()