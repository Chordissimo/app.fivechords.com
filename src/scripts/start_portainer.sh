#!/bin/bash

if [[ $1 == "" ]]; then
  echo
  echo "Error: path to SSL cert is was not provided."
  echo
  echo "Usage: sh ssl_setup.sh <path_to_ssl>"
  echo "<path_to_ssl> - /home/ci_user/.certbot/conf/live/app.fivchords.com"
  echo
  exit 1
fi

sudo docker run -d -p 8001:8001 -p 9443:9443 \
        --name portainer \
        --restart=always \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v portainer_data:/data \
        -v /home/ci_user/.certbot/conf/live/production.aichords.pro:/certs/live/production.aichords.pro:ro \
        -v /home/ci_user/.certbot/conf/archive/production.aichords.pro:/certs/archive/production.aichords.pro:ro \
        portainer/portainer-ce:latest \
        --sslcert /certs/live/production.aichords.pro/fullchain.pem \
        --sslkey /certs/live/production.aichords.pro/privkey.pem \
