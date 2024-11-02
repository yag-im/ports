# https://winworldpc.com/download/c3b7c3bb-07c3-b3cb-8657-11c3a6e28094

# https://dosbox-x.com/wiki/Guide:Installing-Windows-95

cd /mnt/ports_data/runners/src/win98/osrXX-lng

# bootstrap

dosbox-x -conf win95-bootstrap.conf

# key for OSR 2.5: 24995-OEM-0700707-37345

# select only 5 multimedia components:
#   - Audio compression
#   - Media player
#   - Sound recorder
#   - Video compression
#   - Volume control

# after reboot - use win95-install.conf:

dosbox-x -conf win95-install.conf

# Win 95 OSR 2.1 RU
# https://winworldpc.com/download/d2f647d1-4f37-11ec-b881-0200008a0da4
# seems there wasn't 2.5 version published yet

# key for OSR 2.1: 24796-OEM-0014736-66386
