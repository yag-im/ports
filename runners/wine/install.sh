#!/usr/bin/env bash

set -eux

# it's important to create wine prefix from within a docker container
# otherwise wine versions will differ and config update will take place when app is running first time

CUR_DIR=$(cd `dirname $0` && pwd)

# USER is important when creating "Documents" etc folders inside the WINEPREFIX
export USER=gamer
export WINEARCH=win32
export WINE_VER=10.0
export WINEPREFIX="$DATA_DIR/runners/bundles/wine/$WINE_VER/$WINEARCH"
export WINEDLLOVERRIDES='mscoree=d,mshtml=d'

rm -rf $WINEPREFIX && mkdir -p $WINEPREFIX
wine wineboot --init

winetricks win7

# do not include "UseXVidMode"="N" into patch.reg! golden-gate will not start
# wine regedit $CUR_DIR/patch.reg

# should come last, otherwise e.g. $CUR_DIR/patch.reg becomes inaccessible
winetricks sandbox
