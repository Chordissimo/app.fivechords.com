#!/bin/bash

sudo docker build --no-cache -t links_loader -f ./Dockerfile.loader . && \
sudo docker run -d --name links_loader --network src_fivechords links_loader
