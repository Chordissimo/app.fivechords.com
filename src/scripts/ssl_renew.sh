#!/bin/sh
sudo docker compose -f /home/ci_user/app/config/certbot/docker-compose.certbot-renew.yml up -d
sudo ENV=$1 docker compose -f /home/ci_user/app/docker-compose.yml up -d nginx
