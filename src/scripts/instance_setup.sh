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
ln -s  /mongodb/bin/* /usr/local/bin/ && \

cp $BASE_DIR/config/mongo/mongod /etc/init.d && \
chmod +x /etc/init.d/mongod && \
mkdir -p $BASE_DIR/mongodb && \
mkdir -p /var/log/mongodb && \

# ------------ Nginx installation ------------
apt install -y nginx &&\

cp /workspace/config/nginx/default.conf /etc/nginx/conf.d/ && \

mkdir -p /etc/nginx/inc && \
cp $BASE_DIR/config/nginx/headers.conf /etc/nginx/inc/ && \
cp $BASE_DIR/config/nginx/auth.conf /etc/nginx/inc/ && \

# ------------ Gunicorn installation ------------
apt-get -y install supervisor && \
cp $BASE_DIR/config/gunicorn/gunicorn.conf /etc/supervisor/conf.d/ && \
chmod +x $BASE_DIR/config/gunicorn/apid_conf.bash && \
chmod +x $BASE_DIR/config/gunicorn/maind_conf.bash && \
mkdir -p /var/log/5chords && \
pip install --upgrade pip && \
pip install gunicorn && \

# ------------ Application installation ------------
apt-get install -y git "g++" libsndfile1 timidity ffmpeg nginx && \
pip install numpy==1.26.4 wheel "pymongo[srv]" && \
apt install -y libpython3.10-dev && \
pip install --ignore-requires-python chord-extractor==0.1.2 && \
pip install --no-cache-dir -r $BASE_DIR/scripts/requirements.txt && \

# ------------ Download model ------------
mkdir -p $BASE_DIR/model_snapshot && \
python3 $BASE_DIR/snapshot_download.py &&\

# ------------ Chords to nginx ------------
mkdir -p /var/www/chords && \
cp $BASE_DIR/config/chords/* /var/www/chords && \

# ------------ Start services ------------
service mongod start && \
mongosh "mongodb://127.0.0.1:27017/aichords" --file config/mongo/mongo-init.js && \

service nginx start && \

service supervisor start && \
service mongod status
service nginx status

sleep 5
supervisorctl status all
