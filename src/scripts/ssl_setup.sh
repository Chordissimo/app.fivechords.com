if [[ $1 == "" ]]; then
  echo "Error: domain name not found."
  echo "Usage: sh ssl_setup.sh <domain_name> <path_to_yaml>"
  echo "<domain_name> - e.g. get.airchords.app"
  echo "<path_to_yaml> - config/certbot/docker-compose.certbot.yaml"
  echo
fi

if [[ $2 == "" ]]; then
  echo "Error: docker compose yaml not found."
  echo "Usage: sh ssl_setup.sh <domain_name> <path_to_yaml>"
  echo "<domain_name> - e.g. get.airchords.app"
  echo "<path_to_yaml> - config/certbot/docker-compose.certbot.yaml"
  echo
fi

sudo DOMAIN=$1 docker compose -f $2 run --rm certbot certonly --dry-run --webroot --webroot-path /var/www/certbot/ -d $1
#(sudo crontab -l ; echo "@monthly sh /home/ci_user/app/scripts/ssl_renew.sh ${1}") | sort - | uniq - | sudo crontab -
