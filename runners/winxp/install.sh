#!/usr/bin/env bash

set -eux

RUNNER_SRC=$DATA_DIR/runners/src/winxp
OS_FLAVOR=winxpsp3
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

qemu-img create -f qcow2 C 2G
guestfish --rw -a C <<EOF
run
part-init /dev/sda mbr
part-add /dev/sda primary 1 -1
mkfs vfat /dev/sda1
set-label /dev/sda1 SYSTEM
EOF

qemu-img create -f qcow2 D 5G
guestfish --rw -a D <<EOF
run
part-init /dev/sda mbr
part-add /dev/sda primary 1 -1
mkfs vfat /dev/sda1
set-label /dev/sda1 DATA
EOF

# During setup, you must delete and recreate the partitions on both C and D.
# The order of actions is critical to ensure correct drive letter assignment:
#   - Delete C:  [D, L]
#   - Delete D:  [D, L]
#   - Create C:  [C]
#   - Create D:  [C]
#
# If you don’t follow this sequence, Windows will assign drive letter E: to D:,
# and D: will not be visible after installation.
#
# When prompted to format drive C:, choose FAT (Quick) instead of NTFS.
# FAT avoids unnecessary features like file permissions and indexing,
# making it leaner and more suitable for Windows XP.

# Avoid using `-cpu host`. Because the cloud CPU differs from the local dev CPU,
# Windows will detect a new processor and will raise a "New hardware has been found" wizard during the first boot.
qemu-system-x86_64 \
  -drive file=C,if=ide,index=0,media=disk,format=qcow2 \
  -drive file=D,if=ide,index=2,media=disk,format=qcow2 \
  -drive file=$RUNNER_SRC/nlite/WinLite-$LANG.iso,if=ide,index=3,media=cdrom \
  --boot d \
  -enable-kvm \
  -cpu "Skylake-Server,model-id=Intel" \
  -m 1024 \
  -net nic,model=rtl8139 \
  -net user \
  -usbdevice tablet \
  -vga virtio \
  -display sdl,full-screen=off,grab-mod=lshift-lctrl-lalt \
  -audiodev pa,id=pa1 \
  -device AC97,audiodev=pa1

# change resolution and color depth utility
guestfish --rw -a C -i <<EOF
copy-in $RUNNER_SRC/utils/QRes.exe /WINDOWS
EOF
