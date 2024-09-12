#!/bin/bash

if [[ $1 == "" || $2 == "" ]]; then
  echo
  echo "Error: path to Certbot `conf` directory and/or domain were not provided."
  echo
  echo "Usage: sh ssl_setup.sh <domain_name> <path_to_certbot_live> with no trailing slash `/`"
  echo "<domain_name> - e.g. app.fivechords.com"
  echo "<path_to_certbot_live> - /home/ci_user/.certbot/conf"
  echo
  exit 1
fi

echo $2/$1

sudo docker run -d -p 8001:8001 -p 9443:9443 \
        --name portainer \
        --restart=always \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v portainer_data:/data \
        -v $2/live/$1:/certs/live/$1:ro \
        -v $2/archive/$1:/certs/archive/$1:ro \
        portainer/portainer-ce:latest \
        --sslcert /certs/live/$1/fullchain.pem \
        --sslkey /certs/live/$1/privkey.pem \
