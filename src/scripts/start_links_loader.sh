#!/bin/bash

sudo docker build --no-cache -t links_loader -f ./Dockerfile.loader . && \
sudo docker run -d links_loader --name links_loader --network src_fivechords
