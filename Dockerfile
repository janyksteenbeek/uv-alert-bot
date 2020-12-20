FROM python:3.8-slim

RUN mkdir -p /usr/src/app 

WORKDIR /usr/src/app 

COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt 
 
COPY . /usr/src/app

EXPOSE 8025

ENTRYPOINT ["python3"]

CMD ["uv_alert_bot.py", "/config/config.yaml"]
