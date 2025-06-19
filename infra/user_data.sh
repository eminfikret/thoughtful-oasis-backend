#!/usr/bin/env bash
sudo su

apt-get update

if ! command -v docker &> /dev/null
then
    apt-get install -y docker.io
    systemctl enable docker
    systemctl start docker
fi

sleep 10

echo "${CI_DEPLOY_PASSWORD}" | docker login -u "${CI_DEPLOY_USER}" --password-stdin "${CI_REGISTRY}"

docker pull "${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}"

docker run -d \
  -e NODE_ENV="${NODE_ENV}" \
  -e POSTGRES_HOST="${DB_HOST}" \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB="${DB_NAME}" \
  -e POSTGRES_USER="${DB_USERNAME}" \
  -e POSTGRES_PASSWORD="${DB_PASSWORD}" \
  -p 8000:8000 \
  "${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}"
