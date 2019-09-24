FROM arm32v7/python:3.7-slim

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY mqtt-loops.py ./

CMD [ "python", "mqtt-loops.py" ]
