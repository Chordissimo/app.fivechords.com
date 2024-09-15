#!/bin/bash

sudo docker build --no-cache -t app_base -f ./Dockerfile.loader . && \
sudo docker run -d links_loader --name links_loader --network fivechords
