from configurations.backendConfig import conf as backendConfigurations
import pymongo
import configparser
import pika


''' mongo command line example
use video_analytics
db.detectorMap.insert({'int':7,'detectorName':'face','url':'http://54.147.229.75:12000/predict'})
db.commonConfig.insert({'vid':'mbean0','path':'/home/dexter/Projects/STY/data/beanstak/mbean2.avi','detectorList':[7]})
db.additionalMap.insert({'detectorName':'car','advanceAlgoName':'carColor','algoUrl':'http://121.0.0.1:7200/predict'})

mongo commonConfig layout
> db.additionalMap.find()
{ "_id" : ObjectId("604b81ea3b0b5c1cb28a2e0b"), "detectorName" : "car", "advanceAlgoName" : "carColor", "algoUrl" : "http://121.0.0.1:7200/predict" }
{ "_id" : ObjectId("604b82253b0b5c1cb28a2e0c"), "detectorName" : "face", "advanceAlgoName" : "RecognitionAGE", "algoUrl" : "http://54.147.229.75:24000/predict" }
> db.detectorMap.find()
{ "_id" : ObjectId("604b80123b0b5c1cb28a2e08"), "int" : 5, "detectorName" : "person", "url" : "http://54.243.224.221:12000/predict" }
{ "_id" : ObjectId("604b80683b0b5c1cb28a2e09"), "int" : 6, "detectorName" : "yoloAllObject2", "url" : "http://54.243.224.221:12000/predict" }
{ "_id" : ObjectId("604b80873b0b5c1cb28a2e0a"), "int" : 7, "detectorName" : "face", "url" : "http://54.147.229.75:12000/predict" }
> db.commonConfig.find()
{ "_id" : ObjectId("604b7ee73b0b5c1cb28a2e04"), "vid" : "mbean0", "path" : "/home/dexter/Projects/STY/data/beanstak/mbean0.avi", "detectorList" : [ 7 ] }
{ "_id" : ObjectId("604b7f3b3b0b5c1cb28a2e05"), "vid" : "mbean1", "path" : "/home/dexter/Projects/STY/data/beanstak/mbean1.avi", "detectorList" : [ 7 ] }
{ "_id" : ObjectId("604b7f3f3b0b5c1cb28a2e06"), "vid" : "mbean2", "path" : "/home/dexter/Projects/STY/data/beanstak/mbean2.avi", "detectorList" : [ 7 ] }
{ "_id" : ObjectId("604b7f443b0b5c1cb28a2e07"), "vid" : "mbean3", "path" : "/home/dexter/Projects/STY/data/beanstak/mbean3.avi", "detectorList" : [ 7 ] }
'''

def allCameraConfigurations():
    '''
    return
    [('mbean0', '/home/dexter/Projects/STY/data/beanstak/mbean0.avi', [('face', 'http://54.147.229.75:12000/predict')]), 
     ('mbean1', '/home/dexter/Projects/STY/data/beanstak/mbean1.avi', [('face', 'http://54.147.229.75:12000/predict')]), 
     ('mbean2', '/home/dexter/Projects/STY/data/beanstak/mbean2.avi', [('face', 'http://54.147.229.75:12000/predict')]), 
     ('mbean3', '/home/dexter/Projects/STY/data/beanstak/mbean3.avi', [('face', 'http://54.147.229.75:12000/predict')])]

    '''
    # client= pymongo.MongoClient(backendConfigurations['mongoLink'])
    with pymongo.MongoClient(backendConfigurations['mongoLink']) as client:
        db= client['video_analytics']
        commonConfig= db['commonConfig']
        detectorMap= db['detectorMap']

        #getting detector mappings
        detectorDict= {}
        for dic in detectorMap.find():
            if 'detectorName' in dic:
                detectorDict[dic['int']]=(dic['detectorName'],dic['url'])

        #reading camera credentials and detectors
        commonList=[]
        for dic in commonConfig.find({'is_activated':{'$eq':True}}):
            if 'detectorList' in dic:
                detectorDetails=[]
                for value in dic['detectorList']:
                    detectorDetails.append(detectorDict[value])
                tup= (dic['vid'],dic['path'],detectorDetails)
                commonList.append(tup)
        
        return commonList
    

def cameraConfiguration(cameraName):
    '''
    return
    ('mbean0', '/home/dexter/Projects/STY/data/beanstak/mbean0.avi', [('face', 'http://54.147.229.75:12000/predict')])
    '''
    # client= pymongo.MongoClient(backendConfigurations['mongoLink'])
    with pymongo.MongoClient(backendConfigurations['mongoLink']) as client:
        db= client['video_analytics']
        commonConfig= db['commonConfig']
        detectorMap= db['detectorMap']
        try:
            #getting detector mappings
            detectorDict= {}
            for dic in detectorMap.find():
                if 'detectorName' in dic:
                    detectorDict[dic['int']]=(dic['detectorName'],dic['url'])
            
            dic= commonConfig.find_one({'vid':cameraName,'is_activated':True})

            detectorDetails=[]
            for integer in dic['detectorList']:
                detectorDetails.append(detectorDict[integer])

            tup= (dic['vid'],dic['path'],detectorDetails)
            return tup
        except:
            return False


def additionalMap():
    # client= pymongo.MongoClient(backendConfigurations['mongoLink'])
    with pymongo.MongoClient(backendConfigurations['mongoLink']) as client:
        db= client['video_analytics']
        commonConfig= db['additionalMap']

        mapDict={}
        for dic in commonConfig.find({'is_activated':{'$eq':True}}):
            if 'advanceAlgoName' in dic:
                mapDict[dic['detectorName']]= [dic['advanceAlgoName'],dic['algoUrl']]
        return mapDict


def configureDB():
    try:
        print('[Cons Info] looking at db state...')
        with pymongo.MongoClient(backendConfigurations['mongoLink']) as client:
            if 'video_analytics' in client.list_database_names():
                print("[Cons Info] video_analytics db is present ...")
                db= client['video_analytics']
                for coll in ['commonConfig', 'detectorMap', 'additionalMap']:
                    if coll in db.list_collection_names():
                        pass
                    else:
                        db[coll].insert({})
                pass
            else:
                print("[Cons Info] video_analytics db is not present !... creating one")
                db= client['video_analytics']
                print("[Cons Info] Creating collections commonConfig, detectorMap, additionalMap...")
                for coll in [ db['commonConfig'],db['detectorMap'],db['additionalMap']]:
                    coll.insert({})
        print("[Cons Info] db state is ready ...!!")
    except Exception as e:
        print(f'[Prod ERROR!] {e}')

def rabbitCheck():
    print('[RMQ Info] checking RMQ pika connection ...')
    credit = pika.PlainCredentials(username=backendConfigurations['RMQusername'], password=backendConfigurations['RMQpassword'])
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=backendConfigurations['RMQhost'], credentials=credit))
    channel = connection.channel()    
    print('[RMQ Info] Connection status: ',connection.is_open)
    print('[RMQ Info] Channel status: ',channel.is_open)
    if connection.is_open and channel.is_open:
        print('[RMQ Info] RMQ Connection is OK !!!')
    else:
        print('[RMQ Info] RMQ Connection is not OK !!!')
        raise Exception("Rabbitmq connection is correct !!...")



'''
def cameraConfiguration(cameraName):
    #reading camera credentials and detectors
    cameraConfig= configparser.ConfigParser()
    cameraConfig.read(backendConfigurations['commonConfigPath'])

    #getting detector mappings
    detectorMapping= configparser.ConfigParser()
    detectorMapping.read(backendConfigurations['detectorMapPath'])

    listOfCameras= cameraConfig.sections()

    if cameraName in listOfCameras:
        path= cameraConfig[cameraName]['path']
        detectorListIds= cameraConfig[cameraName]['detectorList']
        detectorListIds= detectorListIds.split(' ')
        
        detectorLists= []
        for idd in detectorListIds:
            detectorName, detectorURL= detectorMapping['IntegerMapping'][idd].split(' ')
            detectorLists.append(tuple([detectorName, detectorURL]))

        return cameraName,path,detectorLists
    else:
        return False    

def allCameraConfigurations():
    config= configparser.ConfigParser()
    config.read(backendConfigurations['commonConfigPath'])
    details= []
    for cameraName in config:
        if cameraName != 'DEFAULT':
            cameraDetail= cameraConfiguration(cameraName)
            if cameraDetail != False:
                details.append(cameraDetail)
    return details


def additionalMap():
    #reading camera credentials and detectors
    cameraConfig= configparser.ConfigParser()
    cameraConfig.read(backendConfigurations['additionalMapPath'])
    output= cameraConfig['AlgoMapping']
    ret= dict()
    for out in output:
        string= output[out].split()
        ret[out]= string
    return ret

'''