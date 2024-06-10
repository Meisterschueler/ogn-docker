#!/usr/bin/env bash

ARCH="$(dpkg --print-architecture)"
HW=$(cat /proc/cpuinfo | grep 'Hardware' | awk '{print $3}')


if [ "$HW" = "BCM2835" ]; then
	# All raspberries have "Hardware : BCM2835"
	# https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#new-style-revision-codes
	# PPPP (bits 12-15): 0: BCM2835, 1: BCM2836, 2: BCM2837, 3: BCM2711, 4: BCM2712
	# Only 0, 1 and 2 have "VideoCore IV" that can be used for GPU_FFT
	REV=$(cat /proc/cpuinfo | grep 'Revision' | awk '{print $3}')
	PPPP=$(echo "$(( ( 0x$REV >> 12 ) & 0xF ))")

	# Support for GPU_FFT is dropped with bookworm (debian 12)
	VERSION_ID=$(lsb_release -a | grep 'Release:' | awk '{print $2}')

	if [ "$PPPP" -le 2 ] && [ "$VERSION_ID" -l 12 ]; then
		URL=http://download.glidernet.org/rpi-gpu/rtlsdr-ogn-bin-RPI-GPU-latest.tgz
	elif [ "$ARCH" = "arm64" ]; then
		URL=http://download.glidernet.org/arm64/rtlsdr-ogn-bin-arm64-latest.tgz
	else
		URL=http://download.glidernet.org/arm/rtlsdr-ogn-bin-ARM-latest.tgz
	fi
elif [ "$ARCH" = "arm64" ]; then
	URL=http://download.glidernet.org/arm64/rtlsdr-ogn-bin-arm64-latest.tgz
elif [ "$ARCH" = "i386" ]; then
	URL=http://download.glidernet.org/x86/rtlsdr-ogn-bin-x86-latest.tgz
elif [ "$ARCH" = "amd64" ]; then
	URL=http://download.glidernet.org/x64/rtlsdr-ogn-bin-x64-latest.tgz
elif [ "$ARCH" = "armhf" ]; then
	URL=http://download.glidernet.org/arm/rtlsdr-ogn-bin-ARM-latest.tgz
else
	echo "Architecture '$ARCH' is unknown..."
	exit 1
fi

echo "Download $URL"
wget --no-check-certificate -qO- $URL | tar xvz
