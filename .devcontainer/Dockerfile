ARG DEBIAN_VER=trixie
# https://mcr.microsoft.com/en-us/artifact/mar/devcontainers/python/tags
# TODO: guestfs is incompatible with python > 3.11
FROM mcr.microsoft.com/devcontainers/python:3.11-${DEBIAN_VER}

ARG DOSBOX_VER=0.74-3-5
ARG DOSBOX_X_VER=2024.12.04
ARG DEBIAN_VER
ARG DEBIAN_FRONTEND=noninteractive
ARG USERNAME=vscode

# common
RUN apt-get update \
    && apt install --no-install-recommends -y \
        pulseaudio
RUN usermod -aG audio,video,pulse ${USERNAME}
RUN mkdir /run/user/1000 && chown -R ${USERNAME} /run/user/1000
RUN mkdir -p /home/${USERNAME}/.config/pulse/ \
    && echo "default-server=unix:/tmp/pulseaudio.socket" > /home/${USERNAME}/.config/pulse/client.conf
RUN chown -R ${USERNAME} /home/${USERNAME}
RUN mkdir -p /usr/share/pulse && chown -R ${USERNAME} /usr/share/pulse
COPY files/pulse/default.pa /etc/pulse/default.pa
COPY files/pulse/daemon.conf /etc/pulse/daemon.conf

# dosbox
RUN apt-get install --no-install-recommends -y \
    dosbox=${DOSBOX_VER}+b1

# dosbox-x
RUN apt-get install --no-install-recommends -y \
        automake \
        build-essential \
        ca-certificates \
        git \
        libncurses-dev nasm libsdl-net1.2-dev libsdl2-net-dev libpcap-dev libslirp-dev fluidsynth libfluidsynth-dev \
        libavformat-dev libavcodec-dev libavcodec-extra libswscale-dev libfreetype-dev libxkbfile-dev libxrandr-dev

WORKDIR /tmp

RUN git clone --depth 1 --single-branch --branch dosbox-x-v${DOSBOX_X_VER} https://github.com/joncampbell123/dosbox-x.git

RUN cd ./dosbox-x \
    && ./build-sdl2 \
    && make install

# wine

ARG BUILD_DIR=/tmp/build
ARG PACKAGES_DIR=/tmp/packages
ARG SRC_DIR=/tmp/src

ARG NUM_BUILD_WORKERS=8
ARG WINE_VER=10.0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        automake \
        bison \
        build-essential \
        ca-certificates \
        flex \
        gcc-multilib \
        gettext \
        git

WORKDIR ${SRC_DIR}

RUN git clone --depth 1 --single-branch --branch wine-${WINE_VER} https://github.com/wine-mirror/wine.git
# honor drive type reported by mounts manager (configured through the wincfg)
# otherwise GetDriveTypeW() returns DRIVE_REMOTE for NFS mounted directories while we want them as DRIVE_CDROM
# also adds support for custom CD-ROM labels (also defined through the winecfg)
COPY files/patches/*.patch .
RUN patch ./wine/dlls/kernelbase/volume.c kernelbase-volume.c.patch
RUN patch ./wine/dlls/kernel32/volume.c kernel32-volume.c.patch
RUN patch ./wine/programs/winecfg/driveui.c winecfg-driveui.c.patch

# install wine64 deps
RUN apt-get install -y --no-install-recommends \
    libasound2-dev \
    libfontconfig-dev \
    libfreetype-dev \
    libgl-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libosmesa6-dev \
    libpulse-dev \
    libsdl2-dev \
    libudev-dev \
    libunwind-dev \
    libx11-dev \
    libxcomposite-dev \
    libxcursor-dev \
    libxext-dev \
    libxfixes-dev \
    libxi-dev \
    libxrandr-dev \
    libxrender-dev \
    libxxf86vm-dev

# build wine64
WORKDIR ${BUILD_DIR}/wine64

RUN ${SRC_DIR}/wine/configure \
        --prefix=${PACKAGES_DIR}/wine64 \
        --enable-win64 \
    && make -j${NUM_BUILD_WORKERS} \
    && make install

# install wine32 deps
RUN dpkg --add-architecture i386 \
    && apt-get update
RUN apt-get install -y --no-install-recommends \
    libasound2-dev:i386 \
    libfontconfig-dev:i386 \
    libfreetype-dev:i386 \
    libgl-dev:i386 \
    libgstreamer1.0-dev:i386 \
    libgstreamer-plugins-base1.0-dev:i386 \
    libosmesa6-dev:i386 \
    libpulse-dev:i386 \
    libsdl2-dev:i386 \
    libudev-dev:i386 \
    libunwind-dev:i386 \
    libx11-dev:i386 \
    libxcomposite-dev:i386 \
    libxcursor-dev:i386 \
    libxext-dev:i386 \
    libxfixes-dev:i386 \
    libxi-dev:i386 \
    libxrandr-dev:i386 \
    libxrender-dev:i386 \
    libxxf86vm-dev:i386

# build wine32-tools
WORKDIR ${BUILD_DIR}/wine32-tools

RUN ${SRC_DIR}/wine/configure \
        --prefix=${PACKAGES_DIR}/wine32-tools \
    && make -j${NUM_BUILD_WORKERS} \
    && make install

# build wine32
WORKDIR ${BUILD_DIR}/wine32

RUN ${SRC_DIR}/wine/configure \
        --prefix=${PACKAGES_DIR}/wine32 \
        --with-wine64=${BUILD_DIR}/wine64 \
        --with-wine-tools=${BUILD_DIR}/wine32-tools \
    && make -j${NUM_BUILD_WORKERS} \
    && make install

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        fluidsynth \
        gnupg2 \
        wget

# styrlitz requires avi player (gstreamer1.0-plugins-good:i386) with intel indeo codec (gstreamer1.0-libav:i386)
RUN dpkg --add-architecture i386 \
    && mkdir -pm755 /etc/apt/keyrings \
    && wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key \
    && wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/${DEBIAN_VER}/winehq-${DEBIAN_VER}.sources \
    && apt-get update \
    && apt-get install --install-recommends -y \
        gstreamer1.0-plugins-good:i386 \
        gstreamer1.0-libav:i386 \
        wine-stable \
        winehq-stable \
    && rm -rf /var/lib/apt/lists/*

# install wine32 (should go first) and wine64
RUN rm -rf /opt/wine-stable && mkdir /opt/wine-stable
RUN cp -r ${PACKAGES_DIR}/wine32/* /opt/wine-stable
RUN cp -r ${PACKAGES_DIR}/wine64/* /opt/wine-stable

RUN wget https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks \
    && chmod +x winetricks \
    && mv winetricks /usr/bin

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        7zip \
        gettext \
        innoextract \
        iputils-ping \
        unshield \
        uuid-runtime

# scummvm utils
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        bchunk \
        flac

# qemu
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        qemu-system-gui \
        qemu-system-x86 \
        qemu-utils
# TODO: this doesn't work; we have to set vscode group to 106 explicitly to match hosts' kvm group id
RUN usermod -aG kvm ${USERNAME}

# common
RUN apt install --no-install-recommends -y \
        genisoimage \
        libguestfs-tools \
        libguestfs-dev \
        mtools

WORKDIR /tmp
RUN curl https://poweriso.com/poweriso-x64-1.6.tar.gz -o poweriso-x64-1.6.tar.gz \
    && tar zxvf poweriso-x64-1.6.tar.gz \
    && cp poweriso-x64 /usr/local/bin/poweriso

RUN sed -i '/^Components:/ s/$/ contrib non-free/' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
        unrar
