#!/usr/bin/env bash

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <env> (dev, local or prod)"
  exit 1
fi

ENV_NAME=$1
ENV_DIR="envs/$ENV_NAME"

set -a
. "$ENV_DIR/.env"
set +a

python src/upsert_releases.py
