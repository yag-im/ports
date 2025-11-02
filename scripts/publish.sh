#!/usr/bin/env bash

set -e

IGDB_SLUG=""
RELEASE_UUID=""
STORE_ARGS=""

SCRIPT_NAME=$(basename "$0")

# --- SSH Connection Configuration ---
BASTION_HOST=bastion.yag.im
BASTION_PORT=2207
BASTION_USER=infra
SOCKS_PORT=8022

usage() {
    echo "Usage: $SCRIPT_NAME --igdb-slug=<value> --release-id=<value> [--rm-clones]"
    echo ""
    echo "Options:"
    echo "  --igdb-slug=<value>   Mandatory. IGDB slug."
    echo "  --release-id=<value>  Mandatory. Unique release id (UUID)."
    echo "  --rm-clones           Optional. Removes all clones when enabled."
    echo "  -h, --help            Display this help message and exit."
    exit 1
}

OPTS=$(getopt -o h --long igdb-slug:,release-id:,rm-clones,help -n "$SCRIPT_NAME" -- "$@")

if [ $? != 0 ] ; then
    echo "Error: Failed to parse options." >&2
    usage
fi

# Use 'eval' to assign the output of getopt to positional parameters
eval set -- "$OPTS"

while true; do
    case "$1" in
        --igdb-slug)
            IGDB_SLUG="$2"
            STORE_ARGS+=" $1=$2"
            shift 2
            ;;
        --release-id)
            RELEASE_UUID="$2"
            STORE_ARGS+=" $1=$2"
            shift 2
            ;;
        --rm-clones)
            STORE_ARGS+=" $1"
            shift
            ;;
        -h|--help)
            usage
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Internal error in argument parsing: $1" >&2
            exit 1
            ;;
    esac
done

if [ -z "$IGDB_SLUG" ] || [ -z "$RELEASE_UUID" ]; then
    echo "Error: Both --igdb-slug and --release-id are mandatory." >&2
    usage
fi

set -ux

CUR_DIR=$(cd `dirname "$0"` && pwd)

# upload app bundle to appstor server and app sources to aws S3 glacier
$CUR_DIR/store.sh $STORE_ARGS

# upload media assets to AWS CDN
curl -v --request POST \
  --url "http://portsvc.yag.dc:8087/ports/apps/$IGDB_SLUG/releases/$RELEASE_UUID/publish"

# update prod SQLDB
# SSH tunnel setup: Starts SOCKS proxy in the background
ssh -D $SOCKS_PORT -p $BASTION_PORT -f -N $BASTION_USER@$BASTION_HOST
# Wait for the tunnel to establish
sleep 2

# API call via SOCKS5 proxy
# Using 0:$SOCKS_PORT (localhost:8022) to route the request through the tunnel
curl -v --request POST \
  --socks5-hostname "0:$SOCKS_PORT" "http://portsvc/ports/apps/$IGDB_SLUG/releases/$RELEASE_UUID" \
  --header "content-type: application/x-yaml" \
  --data-binary "@/workspaces/ports/ports/games/$IGDB_SLUG/$RELEASE_UUID.yaml"

# SSH tunnel teardown: Gracefully kill the backgrounded tunnel process
ssh -O exit $BASTION_USER@$BASTION_HOST
