#!/usr/bin/env bash

set -e

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "usage: publish.sh IGDB_SLUG RELEASE_UUID"
    exit 1
fi

set -ux

IGDB_SLUG="$1"
RELEASE_UUID="$2"

CUR_DIR=$(cd `dirname $0` && pwd)

# upload app bundle to appstor server and app sources to aws S3 glacier
$CUR_DIR/store.sh $IGDB_SLUG $RELEASE_UUID

# upload media assets to AWS CDN
curl -v --request POST \
  --url http://portsvc.yag.dc:8087/ports/apps/$IGDB_SLUG/releases/$RELEASE_UUID/publish

# update prod SQLDB
ssh -D 8022 -p 2207 -f -N infra@bastion.yag.im
curl -v --request POST \
  --socks5-hostname 0:8022 "http://portsvc/ports/apps/$IGDB_SLUG/releases/$RELEASE_UUID" \
  --header "content-type: application/x-yaml" \
  --data-binary "@/workspaces/ports/ports/games/$IGDB_SLUG/$RELEASE_UUID.yaml"
ssh -O exit infra@bastion.yag.im
