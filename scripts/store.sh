#!/usr/bin/env bash

# Enable trace mode for debugging
# set -x

# ==============================================================================
# SCRIPT CONFIGURATION
# ==============================================================================

# --- Define Mandatory Variables (Must have a value) ---
IGDB_SLUG=""
RELEASE_ID=""

# --- Define Optional Flags ---
RM_CLONES=false

DATA_DIR="${DATA_DIR:-/mnt/data}"
SEVENZ_EXEC="${SEVENZ_EXEC:-7z}"

# --- Local Paths ---
LOCAL_APPS_DIR="$DATA_DIR/apps"
LOCAL_APPS_SRC_DIR="$DATA_DIR/apps_src"
LOCAL_APPS_TMP_DIR="$DATA_DIR/tmp"

# --- Connection Config ---
BASTION_KEY_PATH=/workspaces/ports/.devcontainer/secrets/id_ed25519
BASTION_HOST=bastion.yag.im
BASTION_PORT=2207
BASTION_USER=infra

# --- AWS Config ---
AWS_PROFILE=yag-prod
AWS_BUCKET_NAME=yag-im-ports

# --- Appstor Config ---
# first host is a master appstor node (us-east-1)
APPSTOR_HOSTS="192.168.12.200,192.168.13.200"
APPSTOR_USER=debian
APPSTOR_APPS_PATH=/opt/yag/data/appstor/apps
APPSTOR_CLONES_PATH=/opt/yag/data/appstor/clones
APPSTOR_TMP_PATH=/tmp

APP_ARCH_NAME=""

SCRIPT_NAME=$(basename "$0")

# ==============================================================================
# USAGE FUNCTION
# ==============================================================================

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

# ==============================================================================
# ARGUMENT PARSING using getopt
# ==============================================================================

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
            shift 2
            ;;
        --release-id)
            RELEASE_ID="$2"
            APP_ARCH_NAME="app_$RELEASE_ID.tar.xz"
            shift 2
            ;;
        --rm-clones)
            RM_CLONES=true
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

# ==============================================================================
# VALIDATION OF MANDATORY ARGUMENTS
# ==============================================================================

if [ -z "$IGDB_SLUG" ] || [ -z "$RELEASE_ID" ]; then
    echo "Error: Both --igdb-slug and --release-id are mandatory." >&2
    usage
fi

# Stop script immediately on non-zero exit code, uninitialized variable, and pipe failure.
set -euo pipefail

# ==============================================================================
# MAIN SCRIPT LOGIC
# ==============================================================================

# --- Host Array Setup ---
IFS=',' read -r -a APPSTOR_HOSTS_ARRAY <<< "$APPSTOR_HOSTS"
MASTER_APPSTOR_HOST="${APPSTOR_HOSTS_ARRAY[0]}"

echo "--- Deployment Target: $MASTER_APPSTOR_HOST ---"

# 1. Archive the app locally
echo "Archiving app to: $LOCAL_APPS_TMP_DIR/$APP_ARCH_NAME"
tar -I "xz -9 -T 0 -v" -cvf "$LOCAL_APPS_TMP_DIR/$APP_ARCH_NAME" \
    -C "$LOCAL_APPS_DIR/$IGDB_SLUG/$RELEASE_ID" \
    --strip-components 1 .

# 2. Copy archived app to appstor
echo "Copying archive to appstor host..."
rsync -ahr --progress \
    -e "ssh -i $BASTION_KEY_PATH -o ServerAliveInterval=10 -J $BASTION_USER@$BASTION_HOST:$BASTION_PORT" \
    "$LOCAL_APPS_TMP_DIR/$APP_ARCH_NAME" \
    "$APPSTOR_USER@$MASTER_APPSTOR_HOST:$APPSTOR_TMP_PATH"

# 3. Unpack app in appstor
echo "Unpacking app on appstor host..."
ssh -i "$BASTION_KEY_PATH" \
    -o ServerAliveInterval=10 \
    -J "$BASTION_USER@$BASTION_HOST:$BASTION_PORT" \
    "$APPSTOR_USER@$MASTER_APPSTOR_HOST" \
    "rm -rf \"$APPSTOR_APPS_PATH/$IGDB_SLUG/$RELEASE_ID\" && \
     mkdir -p \"$APPSTOR_APPS_PATH/$IGDB_SLUG/$RELEASE_ID\" && \
     tar -xvf \"$APPSTOR_TMP_PATH/$APP_ARCH_NAME\" -C \"$APPSTOR_APPS_PATH/$IGDB_SLUG/$RELEASE_ID\" && \
     rm \"$APPSTOR_TMP_PATH/$APP_ARCH_NAME\""

# 4. Clone Removal Logic
if $RM_CLONES; then
    echo "Clones removal enabled. Cleaning up clones on all hosts."
    for HOST in "${APPSTOR_HOSTS_ARRAY[@]}"; do
        echo "  - Removing clones for $IGDB_SLUG on host $HOST"
        ssh -i "$BASTION_KEY_PATH" \
            -o ServerAliveInterval=10 \
            -J "$BASTION_USER@$BASTION_HOST:$BASTION_PORT" \
            "$APPSTOR_USER@$HOST" \
            "find \"$APPSTOR_CLONES_PATH\" -type d -name '$IGDB_SLUG' -exec rm -rf {} +"
    done
fi

# 5. Upload archived sources into the ports storage (S3 Glacier Deep Archive)
LOCAL_SRC_PATH="$LOCAL_APPS_SRC_DIR/$IGDB_SLUG/$RELEASE_ID"
TEMP_7Z_PATH="$LOCAL_APPS_TMP_DIR/$RELEASE_ID.7z"
if [ -d "$LOCAL_SRC_PATH" ]; then
    rm -f "$TEMP_7Z_PATH"
    "$SEVENZ_EXEC" a "$TEMP_7Z_PATH" "$LOCAL_APPS_SRC_DIR/$IGDB_SLUG/$RELEASE_ID"/* -mhc=on -mhe=on -mmt=on -mx9 -t7z
    echo "Uploading sources to S3: s3://$AWS_BUCKET_NAME/$IGDB_SLUG/$RELEASE_ID.7z"
    AWS_PROFILE=$AWS_PROFILE aws s3 cp "$TEMP_7Z_PATH" "s3://$AWS_BUCKET_NAME/$IGDB_SLUG/$RELEASE_ID.7z"
else
    echo "Warning: Source directory $LOCAL_SRC_PATH does not exist (exo port?). Skipping 7z and S3 upload."
fi

exit 0
