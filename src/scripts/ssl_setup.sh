echo "Usage: sh ssl_setup.sh <env>"
echo "env - can be production or staging"
echo
sudo ENV=$1 docker compose -f /home/ci_user/app/config/certbot/docker-compose.certbot-renew.yml run --rm certbot certonly --dry-run --webroot --webroot-path /var/www/certbot/ -d $1.aichords.pro
(sudo crontab -l ; echo "@monthly sh /home/ci_user/app/scripts/ssl_renew.sh ${1}") | sort - | uniq - | sudo crontab -
