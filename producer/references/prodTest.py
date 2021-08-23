import signal
import pika
import concurrent.futures
import sys
import traceback
import os
import cv2
import traceback
import time

def die_peacefully(signal, frame):
    print ('You pressed Ctrl+C - or killed me with -2')
    #.... Put your logic here .....
    os._exit(1)

signal.signal(signal.SIGINT, die_peacefully)


RMQusername= 'test'
RMQpassword= 'test'
RMQhost= 'localhost'
RMQexchangeType= 'topic'

credentials = pika.PlainCredentials(RMQusername,RMQpassword)
connection= pika.BlockingConnection(pika.ConnectionParameters(host=RMQhost, credentials= credentials))
channel= connection.channel()

cameraName= 'hello'
channel.exchange_declare(cameraName, durable=True, exchange_type=RMQexchangeType)
channel.queue_declare(queue= cameraName)
channel.queue_bind(exchange=cameraName, queue=cameraName, routing_key=cameraName)  
channel.basic_publish(exchange=cameraName,routing_key=cameraName,body= 'hello')

for _ in range(5):
    channel.basic_publish(exchange=cameraName,routing_key=cameraName,body= 'hello')
    time.sleep(2)