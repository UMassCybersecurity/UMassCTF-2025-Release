FROM python:alpine3.19

RUN pip install websockets

# Copy assets needed.
COPY src /app

WORKDIR /app/src
EXPOSE 8765

CMD ["python3", "make_firmware.py"]
CMD ["python3", "server.py"]
