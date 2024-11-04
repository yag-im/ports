# https://archive.org/download/microsoft-windows-98-second-edition-oem-x05-29232/Microsoft%20Windows%2098%20Second%20Edition%20OEM%20%5BX05-29232%5D.iso
# https://winworldpc.com/product/windows-98/98-second-edition

# https://dosbox-x.com/wiki/Guide:Installing-Windows-98

cd $DATA_DIR/runners/src/win98

# bootstrap

dosbox-x -conf win98-bootstrap.conf
IMGMAKE C -t hd -size 512

IMGMOUNT C C
IMGMOUNT D win98se.iso
IMGMOUNT A -bootcd D
BOOT A:

# after reboot - continue installation

dosbox-x -c "IMGMOUNT D win98se.iso" -conf win98se.conf

# key VMGGK-72FPD-2PHRP-3HV4R-FYJQJ

# boot again to tune-up the system (see README.md)

dosbox-x -conf win98se.conf
