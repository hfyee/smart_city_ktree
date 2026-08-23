#!/bin/bash
# Sets up Docker and runs chromadb, mongodb and neo4j as containers on the
# dedicated DB host, with persistent storage on the attached data volume.
#
# ASSUMPTION: this instance has outbound internet access (the Internet
# Gateway being added to the VPC separately, ap-southeast-1, plus a public
# IP or NAT). Without egress this script will fail at `dnf install docker`
# and the `docker pull` steps.

set -euxo pipefail

# --- format & mount the dedicated data volume at /data ---------------------
DATA_DEV=/dev/xvdb
DATA_MOUNT=/data
if [ -e "$DATA_DEV" ] && ! blkid "$DATA_DEV" >/dev/null 2>&1; then
  mkfs -t xfs "$DATA_DEV"
fi
mkdir -p "$DATA_MOUNT"
grep -q "$DATA_DEV" /etc/fstab || echo "$DATA_DEV $DATA_MOUNT xfs defaults,nofail 0 2" >> /etc/fstab
mount -a

mkdir -p "$DATA_MOUNT"/{mongodb,neo4j/data,neo4j/logs,chromadb}

# --- Docker -----------------------------------------------------------------
dnf update -y
dnf install -y docker
systemctl enable --now docker

curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# --- docker-compose stack ----------------------------------------------------
cat >/opt/db-docker-compose.yml <<'YAML'
services:
  mongodb:
    image: mongo:7
    container_name: mongodb
    restart: unless-stopped
    ports:
      - "27017:27017"
    volumes:
      - /data/mongodb:/data/db

  neo4j:
    image: neo4j:5
    container_name: neo4j
    restart: unless-stopped
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/${neo4j_password}
    volumes:
      - /data/neo4j/data:/data
      - /data/neo4j/logs:/logs

  chromadb:
    image: chromadb/chroma:latest
    container_name: chromadb
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - /data/chromadb:/chroma/chroma
YAML

/usr/local/bin/docker-compose -f /opt/db-docker-compose.yml up -d
