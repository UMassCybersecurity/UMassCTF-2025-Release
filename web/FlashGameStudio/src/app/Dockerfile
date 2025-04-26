FROM python:slim
RUN pip3 install flask[async] RestrictedPython psycopg2-binary selenium
RUN apt-get update
RUN apt-get install -y wget
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb 
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
WORKDIR /app
COPY app .
RUN chmod +x entrypoint.sh
ENTRYPOINT "/app/entrypoint.sh"