# VideoAnalytics
Automated project for object detection, tracking and analytics

# How to run?
#### 1. Add/Update Camera Configurations and detector API mappings
* **Camera Configurations file > configurations/commonConfig.ini**
* **syntax:-**

| [cameraName]<br>path = cameraPath<br>detectorList = i j k.... |
|---------------------------------------------------------------|

* **example:-**

| example                                                                        |
|--------------------------------------------------------------------------------|
| [mobileCam1]<br>path = http://192.168.0.102:8080/video<br>detectorList = 1 2 6 |
| [webcam1]<br>path = 0<br>detectorList = 4                                      |

#### 2. Detector API mappings
* file > configurations/detectorMap.ini
* **syntax:-**

| [IntegerMapping]<br>i = detector_name detector_API_http_location |
|------------------------------------------------------------------|

* **example**

| [IntegerMapping]                          |
|-------------------------------------------|
| 1 = bag http://121.0.0.1:7001/predict     |
| 2 = gun http://46.34.125.111:7500/predict |
| 3 = car http://121.0.0.1:7200/predict     |

#### 3. Run the project

* **If First time running the project**
It will be better if there is seperate environment for the project else base env is also fine
pip install -r requirements.txt

* **Finally run the program**
python producer.py
python consumer.py
