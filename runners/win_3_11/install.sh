#!/usr/bin/env bash

RUNNERS_BASE_DIR=/mnt/ports_data/runners
RUNNERS_SRC_DIR=$RUNNERS_BASE_DIR/src
WIN311_SRC_DIR=$RUNNERS_SRC_DIR/win311

mkdir -p $WIN311_SRC_DIR

mkdir -p $WIN311_SRC_DIR/drivers/mouse
mkdir -p $WIN311_SRC_DIR/drivers/s3
mkdir -p $WIN311_SRC_DIR/drivers/soundblaster
mkdir -p $WIN311_SRC_DIR/utils
mkdir -p $WIN311_SRC_DIR/multimedia/quicktime

cd $WIN311_SRC_DIR/drivers/mouse
wget https://github.com/joncampbell123/doslib/releases/download/doslib-20201013-2322/doslib-20201013-201731-commit-3ded9ec3dcb06ff97d55cb43051cd5336fc93ce6-binary.tar.xz -O doslib.tar.xz
tar -xf doslib.tar.xz
cp doslib/windrv/dosboxpi/bin/win31/* .

cd $WIN311_SRC_DIR/drivers/soundblaster
wget https://www.dropbox.com/s/0ve3ohhtks0wrnf/SB16W3x.zip?dl=1 -O SB16W3x.zip
unzip SB16W3x.zip -d SB16W3x

cd $WIN311_SRC_DIR/drivers/s3
# http://vogonsdrivers.com/getfile.php?fileid=275
wget https://www.dropbox.com/s/w3o4v5e7alm1zg5/s3drivers.zip?dl=1 -O s3drivers.zip
unzip s3drivers.zip -d s3drivers

cd $WIN311_SRC_DIR/multimedia/quicktime
wget https://www.dropbox.com/s/uimnc5wd4o62sg7/qteasy16.exe?dl=1 -O qteasy16.exe

cd $WIN311_SRC_DIR/utils
wget https://github.com/rayrapetyan/runexit/files/15227813/RUNEXIT.ZIP -O RUNEXIT.ZIP
unzip RUNEXIT.ZIP

cd $WIN311_SRC_DIR
wget https://archive.org/download/windows-3.11/Windows%203.11.iso -O win3.11-en.iso
wget https://archive.org/download/windows_3.11_en-de-ru-tr_with_ms-dos_6.22_eng./Windows%203.11%20Russian.iso -O win3.11-ru.iso

echo "proceed with manual steps from docs/RUNNERS.md (win311 section)"

exit 0
