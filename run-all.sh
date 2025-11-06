#!/bin/zsh

docker network ls | grep -E "\snyabot-netbridge\s" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    docker network create nyabot-netbridge
fi

if [ ! -d "nyabot-dev" ]; then
    git clone git@github.com:ConnectionFailedd/nyabot-dev.git
fi

echo "UID=$(id -u)" > .env
echo "GID=$(id -g)" >> .env

docker compose up -d