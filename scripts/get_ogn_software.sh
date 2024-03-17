ARCH="$(uname -m)"

case "$ARCH" in
    aarch64)    wget download.glidernet.org/arm64/rtlsdr-ogn-bin-arm64-0.3.0.tgz
                tar xfvz rtlsdr-ogn-bin-arm64-0.3.0.tgz
                echo "Fertig..."
                ;;
    *)          echo "Architecture '$ARCH' is unknown..."
                ;;
esac
