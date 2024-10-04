#!/bin/bash

MONGODB_PATH=/mongodb/bin 
CONFIG=/workspace/config/mongo/mongod.conf

exec $MONGODB_PATH/mongod --config $CONFIG