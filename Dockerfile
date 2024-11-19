FROM python:3.10.9-alpine

ENV TG_SESSION="tg_downloader"
ENV TG_API_ID=""
ENV TG_API_HASH=""
ENV TG_BOT_TOKEN=""
ENV TG_DOWNLOAD_PATH=""
ENV TG_MAX_PARALLEL=4
ENV TG_DL_TIMEOUT=5400
ENV TG_AUTHORIZED_USER_ID=""

WORKDIR /app
COPY . /app/
RUN apk update && apk upgrade && apk add build-base && pip install -r requirements.txt
RUN chmod +x tg_downloader.py

ENTRYPOINT ["python"]
CMD ["/app/tg_downloader.py"]
