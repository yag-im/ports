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

# TODO: with scsi drives windows shutdown hangs (bad for UX when user exits any game)
qemu-system-x86_64 \
  -nodefaults \
  -drive file=C,if=ide,index=0,media=disk,format=qcow2 \
  -drive file=D,if=ide,index=1,media=disk,format=qcow2 \
  -drive file=$RUNNER_SRC/$OS_FLAVOR-$LANG/qemu/win98qi_v1.0.1a_ALL.iso,if=ide,index=2,media=cdrom \
  --boot d \
  -enable-kvm \
  -cpu pentium2-v1 \
  -m 256 \
  -M pc,hpet=off,acpi=on,usb=on,accel=kvm \
  -display sdl \
  -device VGA,vgamem_mb=64 \
  -audiodev pa,id=pa1 \
  -device AC97,audiodev=pa1 \
  -usbdevice tablet

# Choose "Windows 98SE, 98Lite Micro" image
# Format C: and D: and create primary partitions on both drives (new -> primary -> write -> quit)
# After first reboot, install "Sound Blaster 16 or AWE32" driver (secondary audio for certain games)
# Shut-down to run next step: tune OS and install drivers from deps.iso below

# deps install
qemu-system-x86_64 \
  -nodefaults \
  -drive file=C,if=ide,index=0,media=disk,format=qcow2 \
  -drive file=D,if=ide,index=1,media=disk,format=qcow2 \
  -drive file=$RUNNER_SRC/$OS_FLAVOR-$LANG/qemu/deps.iso,if=ide,index=2,media=cdrom \
  -enable-kvm \
  -cpu pentium2-v1 \
  -m 256 \
  -M pc,hpet=off,acpi=on,usb=on,accel=kvm \
  -display sdl \
  -device VGA,vgamem_mb=64 \
  -audiodev pa,id=pa1 \
  -device AC97,audiodev=pa1 \
  -usbdevice tablet
