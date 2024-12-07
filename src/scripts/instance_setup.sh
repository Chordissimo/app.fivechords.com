BASE_DIR=/workspace
# ------------ General utilities installation ------------
apt-get update && \
apt-get install -y git-all curl nano gnupg netcat && \

# ------------ MongoDB installation ------------
apt-get install -y libcurl4 libgssapi-krb5-2 libldap-2.5-0 libwrap0 libsasl2-2 libsasl2-modules libsasl2-modules-gssapi-mit openssl liblzma5 && \

curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor && \
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
tee /etc/apt/sources.list.d/mongodb-org-7.0.list && \

apt-get update && \
apt-get install -y mongodb-mongosh && \

mkdir -p /mongodb && \
wget --directory-prefix=/mongodb https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu2204-8.0.0.tgz && \
tar -xf /mongodb/mongodb-linux-x86_64-ubuntu2204-8.0.0.tgz --strip-components=1 -C /mongodb && \
chown -R root:root /mongodb && \
ln -nsf  /mongodb/bin/* /usr/local/bin/ && \

mkdir -p $BASE_DIR/mongodb && \
mkdir -p /var/log/mongodb && \

# ------------ Nginx installation ------------
apt install -y nginx &&\

cp /workspace/config/nginx/default.conf /etc/nginx/conf.d/ && \

mkdir -p /etc/nginx/inc && \
cp $BASE_DIR/config/nginx/headers.conf /etc/nginx/inc/ && \
cp $BASE_DIR/config/nginx/auth.conf /etc/nginx/inc/ && \

# ------------ Supervisor installation ------------
apt-get -y install supervisor && \
cp $BASE_DIR/config/supervisor/supervisord.conf /etc/supervisor/conf.d/ && \
chmod +x $BASE_DIR/config/supervisor/apid_conf.bash && \
chmod +x $BASE_DIR/config/supervisor/maind_conf.bash && \
chmod +x $BASE_DIR/config/supervisor/mongod_conf.bash && \
mkdir -p /var/log/5chords && \

# ------------ Application installation ------------
pip install --upgrade pip && \
apt-get install -y git "g++" libsndfile1 timidity ffmpeg nginx && \
pip install gunicorn numpy==1.26.4 wheel "pymongo[srv]" && \
apt install -y libpython3.10-dev && \
pip install --ignore-requires-python chord-extractor==0.1.2 && \
pip install -U demucs && \
pip install --no-cache-dir -r $BASE_DIR/scripts/requirements.txt && \

# ------------ Download model ------------
mkdir -p $BASE_DIR/model_snapshot && \
python3 $BASE_DIR/snapshot_download.py &&\

# ------------ Chords to nginx ------------
mkdir -p /var/www/chords && \
cp $BASE_DIR/config/chords/* /var/www/chords && \

# ------------ Start services ------------
service nginx start && \
systemctl enable supervisor && \
service supervisor start && \
supervisorctl update && \
sleep 5
mongosh "mongodb://127.0.0.1:27017/aichords" --file config/mongo/mongo-init.js && \
supervisorctl status all
service nginx status
