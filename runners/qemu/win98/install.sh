#!/usr/bin/env bash

set -eux

RUNNER_SRC=$DATA_DIR/runners/src/win9x
OS_FLAVOR=win98se
LANG=""

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 [en|ru]"
  exit 1
fi

case "$1" in
  en|ru)
    LANG="$1"
    ;;
  *)
    echo "Usage: $0 [en|ru]"
    exit 1
    ;;
esac

RUNNER_BUNDLE=$DATA_DIR/runners/bundles/qemu/$OS_FLAVOR-$LANG
cd $RUNNER_BUNDLE

qemu-img create -f qcow2 C 1G
qemu-img create -f qcow2 D 5G

qemu-system-x86_64 \
  -drive file=C,if=ide,index=0,media=disk,format=qcow2 \
  -drive file=D,if=ide,index=1,media=disk,format=qcow2 \
  -drive file=$RUNNER_SRC/$OS_FLAVOR-$LANG/qemu/win98qi_v0.9.6_ALL.iso,if=ide,index=2,media=cdrom \
  --boot d \
  -enable-kvm \
  -cpu pentium2-v1 \
  -m 256 \
  -audiodev pa,id=pa1 \
  -device AC97,audiodev=pa1 \
  -display sdl \
  -device VGA \
  -usbdevice tablet

# Format C: and D: and create primary partitions on both drives;
# Choose "Stock" image (micro image lacks PCI devices: https://github.com/oerg866/win98-quickinstall/issues/25, TODO)
# Choose "Full harwdare detection", otherwise OS will fail with protection error message on first boot
# After installation, shut-down immeditately to run next step: tune OS and install drivers from deps.iso below

# deps install
qemu-system-x86_64 \
  -drive file=C,if=ide,index=0,media=disk,format=qcow2 \
  -drive file=D,if=ide,index=1,media=disk,format=qcow2 \
  -drive file=$RUNNER_SRC/$OS_FLAVOR-$LANG/qemu/deps.iso,if=ide,index=2,media=cdrom \
  -enable-kvm \
  -cpu pentium2-v1 \
  -m 256 \
  -audiodev pa,id=pa1 \
  -device AC97,audiodev=pa1 \
  -display sdl \
  -device VGA \
  -usbdevice tablet
