FROM python:3.7

WORKDIR /videoanalytic

RUN apt update

RUN apt install -y libgl1-mesa-dev

COPY ./requirements.txt /requirements.txt

COPY . .

RUN pip install -U pip wheel cmake

RUN pip install --no-cache -r requirements.txt

EXPOSE 8080

CMD [ "python" , "producer.py" ]
