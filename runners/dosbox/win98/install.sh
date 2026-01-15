# https://archive.org/download/microsoft-windows-98-second-edition-oem-x05-29232/Microsoft%20Windows%2098%20Second%20Edition%20OEM%20%5BX05-29232%5D.iso
# https://winworldpc.com/product/windows-98/98-second-edition

# https://dosbox-x.com/wiki/Guide:Installing-Windows-98

RUNNER_SRC=$DATA_DIR/runners/src/win9x
OS_FLAVOR=win98se
LANG=""

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 [en|ru|ja]"
  exit 1
fi

case "$1" in
  en|ru|ja)
    LANG="$1"
    ;;
  *)
    echo "Usage: $0 [en|ru|ja]"
    exit 1
    ;;
esac

cd $DATA_DIR/runners/src/win9x/win98se-$LANG/dosbox-x

# bootstrap

dosbox-x -conf win98-bootstrap.conf

# Type manually in dosbox prompt:

# IMGMAKE C -t hd -size 512
# IMGMOUNT C C
# IMGMOUNT D ../win98se.iso
# IMGMOUNT A -bootcd D
# BOOT A:

# after reboot - continue installation

dosbox-x -c "IMGMOUNT D ../win98se.iso" -conf win98se.conf

# key VMGGK-72FPD-2PHRP-3HV4R-FYJQJ

# boot again to tune-up the system (see README.md)

dosbox-x -conf win98se.conf
