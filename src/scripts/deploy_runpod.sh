echo "Stopping services..."
service nginx stop && \
supervisorctl stop all && \

echo "Copying config files..."
mkdir -p /etc/nginx/inc && \
cp $BASE_DIR/config/nginx/headers.conf /etc/nginx/inc/ && \
cp $BASE_DIR/config/nginx/auth.conf /etc/nginx/inc/ && \

cp $BASE_DIR/config/supervisor/supervisord.conf /etc/supervisor/conf.d/ && \
chmod +x $BASE_DIR/config/supervisor/apid_conf.bash && \
chmod +x $BASE_DIR/config/supervisor/maind_conf.bash && \
chmod +x $BASE_DIR/config/supervisor/mongod_conf.bash && \

mkdir -p /var/www/chords && \
cp $BASE_DIR/config/chords/* /var/www/chords && \

echo "Starting services..."
service nginx start && \
supervisorctl update && \

echo "Waiting for stauses..."
sleep 5
supervisorctl status all
service nginx status
