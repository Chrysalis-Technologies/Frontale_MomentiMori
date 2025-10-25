FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app/
RUN chmod +x /app/entrypoint.sh
ENV MEDIA_DIR=/data/media \
    SITE_DIR=/app/site \
    TITLE="Memorial Gallery" \
    THUMBNAIL_MAX_PX=480 \
    DISPLAY_MAX_PX=1280 \
    SLIDESHOW_INTERVAL_SEC=6
EXPOSE 8080
ENTRYPOINT ["/app/entrypoint.sh"]