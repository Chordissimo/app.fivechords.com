## CI Workflow 
Normal merge order: Development branch -> Staging -> Master
* To trigger deploy, create and merge a PR with the title starting with `[Release]` where the base branch is `staging` or `master`. Unmerged but closed PRs won't trigger deploy.
* When a PR to staging or master with the title starting with `[Release]` is merged, gitHub action runs `scripts/build_docker.sh` which is responsible for building and running containers. See [scripts/Readme.md](https://github.com/Chordissimo/chords_api_v2/blob/docker-config/scripts/Readme.md)
* **staging.aichords.pro** and **production.aichords.pro** are different instances. Merged PRs to `master` and `staging` will deploy to respective servers.


## Connecting to instances
Private keys can be found here: https://drive.google.com/drive/folders/1X5ClDMR1p2hJKO5iZiMi1h4DLofjkVRT?usp=drive_link
* **Staging** (2 CPU, 4 Gb ram, 50Gb drive), `staging.aichords.pro -> 35.159.4.155`

Admin user (user name: `ubuntu`):
```
ssh -i "staging.pem" ubuntu@ec2-35-159-4-155.eu-central-1.compute.amazonaws.com
```

CI user (user name: `ci_user`):
```
ssh -i "ci_user_staging.pem" ci_user@ec2-35-159-4-155.eu-central-1.compute.amazonaws.com
```
Containers run under `ci_user`, use it for debugging.

**Warning:** If you run containers under ubuntu user, CI will break next time you deploy via GitHub workflow because it won't be able to restart containers (not sure why).


* **Production** (8 CPU, 30Gb ram, Quadro P4000 GPU with 8Gb ram, 100Gb drive), `production.aichords.pro -> 74.82.29.215`

Admin user (user name: `paperspace`):
```
ssh -i “production.pem” paperspace@74.82.29.215
```

CI user (user name: `ci_user`):
```
ssh -i “ci_user_production.pem” ci_user@74.82.29.215
```

Containers run under `ci_user`, use it for debugging.

**Warning:** If you run containers under `paperspace` user, CI will break next time you deploy via GitHub workflow because it won't be able to restart containers (not sure why).


## Staging and Production instances
* Both run the same stack: nginx + certbot + application
* Production instance has GPU therefore has specific drivers and utils installed. See [scripts/Readme.md](https://github.com/Chordissimo/chords_api_v2/blob/docker-config/scripts/Readme.md)

## Application
* `Dockerfile` contains the build instructions for the python application.

## Nginx
* `config/nginx/nginx.conf.template` - nginx configuration for staging and production. The target environment is passed as the environment variable `${ENV}` from the `docker-compose.yml`.
* `config/nginx/auth_staging.cong` and `config/nginx/auth_production.conf` are credentials for swagger (api/docs) in nginx basic auth format. To change password, go to https://8gwifi.org/htpasswd.jsp, copy the SHA256 string and replace the contents of auth config files. 
* `config/nginx/Dockerfile` - accepts the environment variable `${ENV}` from the application Docker file to choose the auth configuration.
Nginx listens to port 443 and 80. The traffic from 80 is redirected to 443. The 80 port is needed to set up and renew the SSL certs, see [scripts/Readme.md](https://github.com/Chordissimo/chords_api_v2/blob/docker-config/scripts/Readme.md) for instructions.
* Nginx accepts 4 locations, method POST (any other methods are denied).
- /docs - swagger, redirects to the application.
- /upload - file upload, redirects to the application.
- /youtube - youtube link, redirects to the application.
- /.well-known/challenge - Letsencrypt SSL install.
- /mongo - mongodb admin UI.
- /logs - dozzle lov viewer.
* the number of simultaneuos connections that nginx forwards to the app is limited to 3 for both environments.

## Certbot
* Letsencrypt certbot runs only once after the build, it provides the volume where the SSL cert is available for nginx.
* Renewal of the SSL cert is done every 30 days. See Scripts below. **<-- // to do**

## MongoDB
* Containerized version of mongo and mongo-express (admin web ui).

## Dozzle
* Web UI for container log monitoring.
* Dozzle doesn't store logs anywhere, it's just the UI for real time log monitoring. So, after container restart/rebuild, logs are cleared.

## Monitorix
* Monitorix is a free, open source, lightweight system monitoring tool designed to monitor as many services and system resources as possible.
* It's installed on the host system directly, so there's no docker container for it.
* It runs local webserver on localhost:8082/monitorix
* Nginx redirects requests from *.aichords.pro/monitorix to `host.docker.internal:8082` which is the host that resolves to host machine IP from inside nginx container.

## docker-compose.yml
* `Dockerfile` contains the build instructions for the python application.
* `docker-compose.staging.yml` contains instructions for configuring all containers for staging.
```
services: 
### Application container.
  aichords:

### Image name and container name use ${ENV} just for visual differentiation, nothing will break if you change that.
    image: aichords_${ENV}
    container_name: aichords_${ENV}

### not sure what the "restart" option does exactly. 
    restart: always

### the directory where Dockerfile is located
    build: .

### Ports have to be like this, otherwise for some reason the app refuses connections from nginx. Changing it to smth like this 81:8000 doesn't work even when exposit 81 and 8000 in Dockerfile. Not sure why.
    ports:
    - 8000:8000

### The network needs to be the same for nginx and aichords services so that the can be reference by service name as a host name in nginx config.
    networks:
    - app_default

### GPU support for production environment
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

### NGINX container
  nginx:
    image: nginx_${ENV}
    container_name: nginx_${ENV}
    restart: always
    build: 
      context: ./config/nginx

### ${ENV} is passed either from the deploy.yml or from the shell. Example: sudo ENV=staging docker compose build
      args:
      - ENV=${ENV}
    volumes:
    - ./config/nginx.conf:/etc/nginx/cong.d/default.conf

### These volumes are for obtaining and storing the SSL cert. Be careful deleting unused volumes.
    - ./certbot/www/:/var/www/certbot:ro
    - ./certbot/conf/:/etc/nginx/ssl/:ro
    ports:
    - 80:80
    - 443:443
    networks:
    - app_default

### The ${ENV} is forwarded to containers and is used in nginx Dockerfile.
    environment:
      ENV: ${ENV}

networks:
  app_default:
```
* `docker-compose.production.yml` contains instructions for configuring all containers for production. The only difference between `docker-compose.staging.yml` and `docker-compose.production.yml` is the GPU support which is only needed for prod. `docker-compose.production.yml` or `docker-compose.staging.yml` is being renamed to `docker-compose.yml` by `scripts/build_docker.sh` when GitHub action is triggered.
* Service names (aichords, nginx, etc) are hostnames which are used by services to interact with each other. Changing service names will require cross-checking the configuration of relevant services.

## config/certbot/docker-compose.certbot-renew.yml
This comopose-file is used by `ssl_renew.sh` to renew ssl cert. It's run monthly by crontab.
```
services:
  certbot:
    image: certbot/certbot:latest
    container_name: certbot
    volumes:
     - ./certbot/www/:/var/www/certbot:rw
     - ./certbot/conf/:/etc/letsencrypt/:rw
    command: certonly --webroot --webroot-path /var/www/certbot/ -d production.aichords.pro --dry-run
```


## Scripts
* `build_docker.sh` - builds and deploys nginx and the app. This script is triggered by the worflow (see [.github/workflows/deploy.yml](https://github.com/Chordissimo/chords_api_v2/blob/docker-config/.github/workflows/deploy.yml)).
* `docker_install.sh` - installs docker and dependencies.
* `GPU_support_part1.sh` and `GPU_support_part2.sh` - installs GPU support.
* `create_ci_user.sh` - creates `ci_user` for specified environment and generates ssh key which needs to be added as a github secret.
* `ssl_setup.sh` - obtains ssl cert from Letsencrypt.
* `ssl_renew.sh` - renews the ssl cert, the scipt is added to crontab and runs monthly. See `sudo crontab -e`.

See [scripts/Readme.md](https://github.com/Chordissimo/chords_api_v2/blob/docker-config/scripts/Readme.md) for detaied instruction on how to set up a fresh server.

## Manual services build, run and stop
**Important:** you must log in as **ci_user**, if you run containers as main user (ubuntu), the build via CI pipeline will crash next time you merge a PR.
* sudo `ENV=<env> SRV="<service_names>" bash scripts/build_docker.sh` - builds containers but doesn't start them.
- `<env>` can be staging or production.
- `<service_names>` is a comma-separated list of services to build: 'nginx,aichords,mongo'. Omitting SRV will trigger full rebuild of all services in docker-compose.yml.
* `ENV=<env> sudo docker compose up -d` - starts all contaners.

**Warning**: do not manually delete images with `sudo docker images rmi <image_id>` because you might delete the certbot image and you will need to generate new SSL certificate to make HTTPS work again. `sudo docker system prune` cleans up everything just fine.
