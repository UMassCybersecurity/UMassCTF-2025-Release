FROM python:slim
RUN pip3 install flask

WORKDIR /app
COPY app ./

ENTRYPOINT ["python3", "./leg.py"]