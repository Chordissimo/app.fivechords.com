#!/bin/bash
set -e

cd /home/ci_user/src
sudo docker builder prune -f && \
sudo cp config/docker/${DOMAIN}.yml ./docker-compose.yml
sudo ln -sf /home/ci_user/.auth ./.auth
sudo ln -sf /home/ci_user/.certbot ./.certbot

if [[ ${SRV} == *"nginx"* ]]; then
  sudo ENV=${ENV} docker compose build nginx --no-cache
  sudo ENV=${ENV} docker compose up -d nginx
fi

if [[ ${SRV} == *"app"* ]]; then
  sudo ENV=${ENV} docker compose build recognizer retriever --no-cache
  sudo ENV=${ENV} docker compose up -d recognizer retriever
fi

if [[ ${SRV} == *"mongo"* ]]; then
  sudo ENV=${ENV} docker compose build mongo mongo-express --no-cache
  sudo ENV=${ENV} docker compose up -d mongo mongo-express
fi

if [[ ${SRV} == ",," ]]; then
  sudo docker build --no-cache -t app_base -f ./Dockerfile.base .
  sudo ENV=${ENV} docker compose build --no-cache
  sudo ENV=${ENV} docker compose up -d
fi

sudo docker system prune -a -f --filter label!="app_base=dont_delete" --volumes
