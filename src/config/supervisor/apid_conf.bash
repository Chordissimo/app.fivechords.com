#!/bin/bash

NAME=apid
DIR=/workspace
USER=root
GROUP=root
WORKERS=10
WORKER_CLASS=uvicorn.workers.UvicornWorker
LOG_LEVEL=info
BIND=127.0.0.1:8002

cd $DIR

exec gunicorn api:app \
  --name $NAME \
  --workers $WORKERS \
  --worker-class $WORKER_CLASS \
  --user $USER \
  --group $GROUP \
  --log-level $LOG_LEVEL \
  --bind $BIND