#!/usr/bin/env bash

set -e

if [ -z "$1" ]; then
    echo "usage: init_port.sh igdb_slug"
    exit 1
fi

set -u

APPS_SRC_ROOT_DIR=$DATA_DIR/apps_src

export APP_RELEASE_UUID=`uuidgen`
export TZ="America/Los_Angeles"
export CURRENT_DATETIME="$(date +"%Y-%m-%d %H:%M:%S") America/Los_Angeles"
export IGDB_SLUG=$1
export PORTS_ROOT_DIR=/workspaces/ports

# create dir for app source files
mkdir -p $APPS_SRC_ROOT_DIR/$IGDB_SLUG/$APP_RELEASE_UUID

# create dir and template for installer
mkdir -p $PORTS_ROOT_DIR/ports/games/$IGDB_SLUG
envsubst < $PORTS_ROOT_DIR/scripts/templates/release.yaml.tmpl > $PORTS_ROOT_DIR/ports/games/$IGDB_SLUG/$APP_RELEASE_UUID.yaml

# update vscode launcher script
envsubst < $PORTS_ROOT_DIR/scripts/templates/launch.json.tmpl > $PORTS_ROOT_DIR/.vscode/launch.json

# create requests.http script
envsubst < $PORTS_ROOT_DIR/scripts/templates/requests.http.tmpl > $PORTS_ROOT_DIR/scripts/tmp/requests.http

# next steps
echo "after updating app descriptor, run:"
echo "curl --request POST \
  --url http://portsvc.yag.dc:8087/ports/apps/$IGDB_SLUG/releases/$APP_RELEASE_UUID \
  --header 'content-type: application/x-yaml' \
  --header 'user-agent: vscode-restclient' \
  --data-binary '@/workspaces/ports/ports/games/$IGDB_SLUG/$APP_RELEASE_UUID.yaml'"
echo "after local testing, run:"
echo "/workspaces/ports/scripts/publish.sh $IGDB_SLUG $APP_RELEASE_UUID"
