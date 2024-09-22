#!/bin/bash

sudo docker exec -ti mongo sh -c "mongosh -u aichords -p 12345 -authenticationDatabase aichords -f dedup.js"
