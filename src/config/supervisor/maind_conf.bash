#!/bin/bash

NAME=maind
DIR=/workspace
USER=root
GROUP=root
WORKERS=1
WORKER_CLASS=uvicorn.workers.UvicornWorker
LOG_LEVEL=info
BIND=127.0.0.1:8000
TIMEOUT=600
LD_LIBRARY_PATH=/usr/local/lib/python3.10/dist-packages/nvidia/cudnn/lib/

cd $DIR

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH

exec gunicorn main:app \
  --name $NAME \
  --workers $WORKERS \
  --worker-class $WORKER_CLASS \
  --timeout $TIMEOUT \
  --user=$USER \
  --group=$GROUP \
  --log-level=$LOG_LEVEL \
  --bind $BIND