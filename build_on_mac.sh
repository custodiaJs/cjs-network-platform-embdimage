#!/bin/bash

# Funktion zum Erkennen der Architektur des Systems
detect_architecture() {
    local arch
    arch=$(uname -m)

    if [[ "$arch" == "x86_64" ]]; then
        ARCH="x86_64"
        CROSS_COMPILE="x86_64-elf-"
        QEMU_SYSTEM="qemu-system-x86_64"
    elif [[ "$arch" == "arm64" ]]; then
        ARCH="arm64"
        CROSS_COMPILE="aarch64-linux-gnu-"
        QEMU_SYSTEM="qemu-system-aarch64"
    else
        echo "Nicht unterstützte Architektur: $arch"
        exit 1
    fi
}

# Kernel-Version festlegen
KERNEL_VERSION="6.5"

# Prüfen, ob Homebrew installiert ist
if ! command -v brew &>/dev/null; then
    echo "Homebrew nicht gefunden. Installiere Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Installiere die benötigten Abhängigkeiten
echo "Installiere benötigte Abhängigkeiten über Homebrew..."
brew install qemu gcc make gnu-sed gawk wget

# Prüfe und installiere die passenden Cross-Compiler
detect_architecture
echo "Architektur erkannt: $ARCH"
if [[ "$ARCH" == "x86_64" ]]; then
    brew install x86_64-elf-gcc
elif [[ "$ARCH" == "arm64" ]]; then
    brew install aarch64-linux-gnu-gcc
fi

# Erstelle und mounte ein case-sensitive Disk-Image
DISK_IMG="$HOME/LinuxKernel.dmg"
DISK_VOL="/Volumes/LinuxKernel"
if [ ! -f "$DISK_IMG" ]; then
    echo "Erstelle case-sensitive Disk-Image..."
    hdiutil create -size 10g -fs "Case-sensitive HFS+" -volname "LinuxKernel" "$DISK_IMG"
fi

echo "Mounten des Disk-Images..."
hdiutil mount "$DISK_IMG"
cd "$DISK_VOL"

# Lade den Linux-Kernel-Quellcode herunter
KERNEL_TAR="linux-${KERNEL_VERSION}.tar.xz"
KERNEL_URL="https://cdn.kernel.org/pub/linux/kernel/v6.x/${KERNEL_TAR}"

echo "Lade Linux-Kernel Version ${KERNEL_VERSION} herunter..."
wget "$KERNEL_URL"
tar -xvf "$KERNEL_TAR"
cd "linux-${KERNEL_VERSION}"

# Konfiguriere den Kernel mit einer minimalen Konfiguration für QEMU
echo "Konfiguriere den Kernel für QEMU..."
if [[ "$ARCH" == "x86_64" ]]; then
    make defconfig
elif [[ "$ARCH" == "arm64" ]]; then
    make defconfig ARCH=arm64
fi

# Kompiliere den Kernel
echo "Kompiliere den Kernel für Architektur ${ARCH}..."
make ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE all -j$(sysctl -n hw.logicalcpu)

# Prüfe, ob der Kernel erfolgreich kompiliert wurde
if [ ! -f "arch/$ARCH/boot/bzImage" ] && [ ! -f "arch/$ARCH/boot/Image" ]; then
    echo "Fehler: Der Kernel wurde nicht erfolgreich kompiliert."
    exit 1
fi

# Unmount das Disk-Image
echo "Unmounting des Disk-Images..."
hdiutil unmount "$DISK_VOL"

echo "Kompilierung abgeschlossen! Kernel ist verfügbar."