# Setting up a fresh server.

## 1. Pre-installation steps docker 
From your local machine, copy the following scripts to the instance.
```
scp -i ci_user_<env>.pem docker_install.sh create_ci_user.sh ci_user@<host>:~
```
In case you are setting up production, copy the following scripts.
```
scp -i ci_user_<env>.pem GPU_support_part1.sh GPU_support_part1.sh ci_user@<host>:~
```
Replace <env> with `staging` or `production`, replace <host> with AWS instance host or Paperspace public IP.

## 2. Installing docker and GPU support.

* Connect to the instance as `ubuntu` for staging or `paperspace` for production, see https://github.com/Chordissimo/chords_api_v2/blob/develop/Readme.md for details.
* Run the following script to install docker and its dependencies:
```
sudo sh ~/server_setup.sh
```
* Next, create `ci_user` which is needed for github workflow to work.
```
sudo bash ./create_ci_user.sh
```
**Important:** use `bash` because it supports redirection, to answer "yes" automatically to questions asked during set up.
The script will display the private key which you need to add as a secret to github. See [.github/workflows/deploy.yml](https://github.com/Chordissimo/chords_api_v2/blob/docker-config/.github/workflows/deploy.yml) for secret naming.
The script will copy created keys to `~/.ci_user_keys`. You need to download private key to your local machine to SSH connect to the instance.

**Important:** in case if you need to re-run this script, you might need to delete previously created user.
```
sudo su
# userdel ci_user
# rm -rf /home/ci_user
# exit
```

* In case you are setting up a production instance, do the following:
Install nvidia drivers.
```
sudo sh ~/GPU_support_part1.sh
```
You must **reboot** the instance after that step.
Once the instance is up, run `nvidia-smi` to check if drivers has been installed successfully.
Install ndvidia docker support.
```
sudo sh ~/GPU_support_part2.sh
```

## 3. Launch containers
We need to get nginx up listening to port 80 to get ssl cert on the next step. 
To achieve this, do the following:
1. Update global environment var SERVER in [.github/workflow/deploy.yml](https://github.com/Chordissimo/chords_api_v2/blob/docker-config/.github/workflows/deploy.yml) with a public IP of the new instance (has to to Elastic IP which doesn't change).
2. Run the workflow by creating a PR with the title starting with `[Release]` to a branch matching target environment, it'll upload the code to the server, will build and run containers.
3. Nginx is going to be failing to load certificate. To fix this: 
* from your local machine log it as `ci_user`
* comment ssl related lines in `config/nginx/nginx.conf.template`
  ```
  nano ~/app/config/nginx/nginx.conf.template
  
  #server {
  #  listen 80;
  #  server_name ${ENV}.aichords.pro;
  #  return 301 https://${ENV}.aichords.pro$request_uri;
  #}

  server {
  #  listen 443 ssl;
    listen 80;   	<--- add this line
  
  ...

  #  ssl_certificate /etc/nginx/ssl/live/${ENV}.aichords.pro/fullchain.pem;
  #  ssl_certificate_key /etc/nginx/ssl/live/${ENV}.aichords.pro/privkey.pem;
  ...
  ```
* re-build nginx
```
cd ~/app
sudo ENV=<env> docker compose build nginx && sudo ENV=<env> docker compose up -d
```
Replace <env> with `staging` or `production`, check if server is up by open `http://<host>/docs` in your browser. Replace <host> with staging.aichords.pro or production.aichords.pro.
 
## 4. Install ssl
**Important:** Before proceeding with the following steps, make sure the host name resolves to the correct IP. If this is not the case, ssl installation will fail.

Using the ssh key log in `as ci_user` and run the ssl script. This will obtain new cert and install it.
* run `sudo sh ~/app/scripts/ssl_setup.sh <host>` - replace `host` with  `staging.aichords.pro` or `production.aichords.pro`
* if successful, uncomment ssl related lines in `config/nginx/nginx.conf.template` and delete `listen 80;` line, and then run
```
sudo ENV=<env> docker compose build nginx
sudo ENV=<env> docker compose up -d`.
```
Replace <env> with `staging` or `production`, check if server is up.
Backup SSL cert.
```
sudo su 
cp /home/ci_user/app/certbot /home/<user>/
```
Replace <user> with `ubuntu` for staging and `paperspace` for production.
Certificate renewal will be done monthly by `ssl_renew.sh` script, the `ssl_install.sh` script adds the endry to the crontab.

## 5. Check server is up.
Visit `https://<env>.aichords.pro`
Replace <env> with environment name: staging or production

## 6. Firewall
Docker bypasses the UFW rules and the published ports can be accessed from outside. Means, even if you disallow external connection, for example, to port 8000 by applying the rule with UFW (Ubuntu firewall), the port 8000 is still accessible from the outside if exposed in Dockerfile. The following fixes it. See [https://github.com/chaifeng/ufw-docker] for details.

* disable ufw
```
sudo ufw disable
```

* Modify the UFW configuration file `/etc/ufw/after.rules` and add the following rules at the end of the file:
```
# BEGIN UFW AND DOCKER
*filter
:ufw-user-forward - [0:0]
:ufw-docker-logging-deny - [0:0]
:DOCKER-USER - [0:0]
-A DOCKER-USER -j ufw-user-forward

-A DOCKER-USER -j RETURN -s 10.0.0.0/8
-A DOCKER-USER -j RETURN -s 172.0.0.0/8
-A DOCKER-USER -j RETURN -s 192.168.0.0/16

-A DOCKER-USER -p udp -m udp --sport 53 --dport 1024:65535 -j RETURN

-A DOCKER-USER -j ufw-docker-logging-deny -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -d 192.168.0.0/16
-A DOCKER-USER -j ufw-docker-logging-deny -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -d 10.0.0.0/8
-A DOCKER-USER -j ufw-docker-logging-deny -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -d 172.0.0.0/8
-A DOCKER-USER -j ufw-docker-logging-deny -p udp -m udp --dport 0:32767 -d 192.168.0.0/16
-A DOCKER-USER -j ufw-docker-logging-deny -p udp -m udp --dport 0:32767 -d 10.0.0.0/8
-A DOCKER-USER -j ufw-docker-logging-deny -p udp -m udp --dport 0:32767 -d 172.0.0.0/8

-A DOCKER-USER -j RETURN

-A ufw-docker-logging-deny -m limit --limit 3/min --limit-burst 10 -j LOG --log-prefix "[UFW DOCKER BLOCK] "
-A ufw-docker-logging-deny -j DROP

COMMIT
# END UFW AND DOCKER
```
* add the following rules to UFW:
```
sudo ufw allow proto tcp from any to any port 22
sudo ufw allow proto tcp from any to any port 80
sudo ufw allow proto tcp from any to any port 443
sudo ufw allow proto tcp from 172.0.0.0/8 to any port 8082
sudo ufw route allow proto tcp from any to any port 22
sudo ufw route allow proto tcp from any to any port 80
sudo ufw route allow proto tcp from any to any port 443
sudo ufw route allow proto tcp from 172.0.0.0/8 to any port 8082
sudo ufw default deny incoming
```

* if ufw is enabled
```
sudo systemctl restart ufw
sudo ufw enable
```

## 7. Troubleshooting
* `sudo docker logs nginx_<env>` - nginx logs.
* `sudo docker ps -a` - running containers.
* `sudo docker network ls` - list of docker networks. There shoud be a network with the name ending on `app_default`. Copy the name of that network.
* `sudo docker inspect network <app_default>` - replace `<app_default>` with the network name. In the output find the Containers section to get IPs of nginx and aichords app. Use those IPs to check if services are responding, for example: `curl 172.18.0.3:8000/api/docs` should give you swagger HTML, assuming that was an IP of aichords app.  

