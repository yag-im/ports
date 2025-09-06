#!/usr/bin/env bash

set -e

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "usage: store_app.sh IGDB_SLUG RELEASE_ID"
    exit 1
fi

set -ux

IGDB_SLUG="$1"
RELEASE_ID="$2"

LOCAL_APPS_DIR=$DATA_DIR/apps
LOCAL_APPS_SRC_DIR=$DATA_DIR/apps_src
LOCAL_APPS_TMP_DIR=$DATA_DIR/tmp

BASTION_KEY_PATH=/workspaces/ports/.devcontainer/secrets/id_ed25519
BASTION_HOST=bastion.yag.im
BASTION_PORT=2207
BASTION_USER=infra

# master appstor node (us-east-1)
APPSTOR_HOST=192.168.12.200
APPSTOR_USER=debian
APPSTOR_APPS_PATH=/opt/yag/data/appstor/apps
APPSTOR_TMP_PATH=/tmp

APP_ARCH_NAME=app_$RELEASE_ID.tar.xz

# upload app into the appstor
# direct nfs copy of many files is slow, so sending an archived copy and unpacking directly on the appstor host
# using tar.xz insted of 7z due to "danger symlinks" unsupported in the latter (e.g. z: -> / is mandatory for .wine)
tar -I "xz -9 -T 0 -v" -cvf $LOCAL_APPS_TMP_DIR/$APP_ARCH_NAME -C $LOCAL_APPS_DIR/$IGDB_SLUG/$RELEASE_ID --strip-components 1 .

# copy archived app to appstor
rsync -ahr --progress \
    -e "ssh -i $BASTION_KEY_PATH -o ServerAliveInterval=10 -o ProxyCommand='ssh -p $BASTION_PORT -W %h:%p $BASTION_USER@$BASTION_HOST'" \
    $LOCAL_APPS_TMP_DIR/$APP_ARCH_NAME \
    $APPSTOR_USER@$APPSTOR_HOST:$APPSTOR_TMP_PATH

# unpack app in appstor
ssh -i $BASTION_KEY_PATH \
    -o ServerAliveInterval=10 \
    -J $BASTION_USER@$BASTION_HOST:$BASTION_PORT \
    $APPSTOR_USER@$APPSTOR_HOST \
    "rm -rf $APPSTOR_APPS_PATH/$IGDB_SLUG/$RELEASE_ID && mkdir -p $APPSTOR_APPS_PATH/$IGDB_SLUG/$RELEASE_ID && tar -xvf $APPSTOR_TMP_PATH/$APP_ARCH_NAME -C $APPSTOR_APPS_PATH/$IGDB_SLUG/$RELEASE_ID && rm $APPSTOR_TMP_PATH/$APP_ARCH_NAME"

# upload archived sources into the ports storage (S3 Glacier Deep Archive)
if [ -d "$LOCAL_APPS_SRC_DIR/$IGDB_SLUG/$RELEASE_ID" ]; then
    rm -f $LOCAL_APPS_TMP_DIR/$RELEASE_ID.7z
    $SEVENZ_EXEC a $LOCAL_APPS_TMP_DIR/$RELEASE_ID.7z $LOCAL_APPS_SRC_DIR/$IGDB_SLUG/$RELEASE_ID/* -mhc=on -mhe=on -mmt=on -mx9 -t7z
    AWS_PROFILE=yag-prod aws s3 cp $LOCAL_APPS_TMP_DIR/$RELEASE_ID.7z s3://yag-im-ports/$IGDB_SLUG/$RELEASE_ID.7z
else
    echo "Warning: Source directory $LOCAL_APPS_SRC_DIR/$IGDB_SLUG/$RELEASE_ID does not exist (exo port?). Skipping 7z and S3 upload."
fi
