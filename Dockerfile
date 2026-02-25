FROM python:3.11.14-alpine3.23

LABEL org.opencontainers.image.authors="https://github.com/bunker-pilot"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt 
COPY ./requirements.dev.text /tmp/requirements.dev.txt
COPY ./app /app

WORKDIR /app

EXPOSE 8000


ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; then \
        /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi &&\
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user &&\
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod 755 /vol

ENV PATH="/py/bin:$PATH"
USER django-user