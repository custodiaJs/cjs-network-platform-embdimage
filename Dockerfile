# Basis-Image: Minimal Debian
FROM debian:latest

# Maintainer Information
LABEL maintainer="mail@example.com"

# Aktualisiere und installiere benötigte Abhängigkeiten
RUN apt-get update && apt-get install -y \
    gcc \
    make \
    wget \
    git \
    libncurses-dev \
    bison \
    flex \
    python3 \
    python3-pip \
    sudo \
    && apt-get clean

# Erstelle ein Verzeichnis für das Skript
WORKDIR /usr/src/app

# Kopiere das Python-Skript in das Verzeichnis des Containers
COPY build_kernel.py .

# Installiere Python-Abhängigkeiten (falls benötigt, aktuell keine)
# RUN pip3 install -r requirements.txt

# Setze das Skript als ausführbar
RUN chmod +x build_kernel.py

# Führe das Skript aus
CMD ["python3", "build_kernel.py"]