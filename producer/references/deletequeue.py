import pika
def delQueue( name):
    RMQusername= 'test'
    RMQpassword= 'test'
    RMQhost= 'localhost'
    #RMQexchange= 'videoStream'
    RMQexchangeType= 'topic'
    credentials = pika.PlainCredentials(RMQusername,RMQpassword)
    connection= pika.BlockingConnection(pika.ConnectionParameters(host=RMQhost, credentials= credentials))
    channel=connection.channel()
    channel.queue_delete(name)
    print(f'[Producer Info] deleted queue {name} ************')

lists= [f'mbean{i}' for i in range(10)]; lists.extend([f'mbean_{i}' for i in range(10)])
for name in lists:
    delQueue(name)
