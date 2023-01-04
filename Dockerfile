FROM python:3.10.9-alpine

WORKDIR /app
COPY . /app/
RUN apk update && apk upgrade && apk add build-base && pip install -r requirements.txt
RUN chmod +x tg_downloader.py

ENTRYPOINT ["python"]
CMD ["/app/tg_downloader.py"]
