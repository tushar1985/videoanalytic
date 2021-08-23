import pymongo

# insertion= False
insertion= True
# deleteall= True 
deleteall= False

viewall= True

def showw(k):
    for i in k:
        print(i)

commonConfigDict={
    "uid" : 13,
    "vid" : 'camera3',
    # "path": 'rtsp://admin:admin123@27.54.41.195/Streaming/Channels/101',
    "path": '/home/ubuntu/invigilioCode/streetWalk.mp4',
    "detectorList": [
        1,
    ],
    "is_activated" : True
	}

detectorMappingDict={	
    "uid" : 11,
    "int" : 1,
    "url" : "http://0.0.0.0:11000/predict",
    "detectorName" : 'dumbDetector'
	}

# addtionalMappingDict= {
#     "uid" : 11,
#     "algourl": "",
#     "detectorName": ,
#     "advancealgoName": ,
# 	}

cli= pymongo.MongoClient('localhost',27017)
db= cli['video_analytics']
print(db.list_collection_names())
commonConfig = db['commonConfig']
detectorMap = db['detectorMap']
additionalMap = db['additionalMap']


if insertion:
    commonConfig.insert(commonConfigDict)
    detectorMap.insert(detectorMappingDict)
    # additionalMap.insert(addtionalMappingDict)

if deleteall:
    commonConfig.delete_many({})
    detectorMap.delete_many({})
    additionalMap.delete_many({})
    commonConfig.insert({})
    detectorMap.insert({})
    additionalMap.insert({})

if viewall:
    print('commonConfig')
    showw(commonConfig.find())
    print('detectorMap')
    showw(detectorMap.find())
    print('additionalMap')
    showw(additionalMap.find())


'''
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