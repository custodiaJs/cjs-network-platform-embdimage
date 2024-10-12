import os
import subprocess
import sys
import shutil

def run_command(command, cwd=None, shell=False):
    """Führt einen Shell-Befehl aus und zeigt die Ausgabe an."""
    print(f"Running command: {' '.join(command) if isinstance(command, list) else command}")
    result = subprocess.run(command, cwd=cwd, shell=shell, check=True)
    return result

def detect_architecture():
    """Erkennt die Architektur des Systems."""
    arch = os.uname().machine
    if arch == "x86_64":
        return "x86_64", "x86_64-elf-"
    elif arch == "arm64":
        return "arm64", "aarch64-linux-gnu-"
    else:
        print(f"Nicht unterstützte Architektur: {arch}")
        sys.exit(1)

def install_dependencies():
    """Installiert benötigte Abhängigkeiten."""
    try:
        run_command(["brew", "install", "qemu", "gcc", "make", "gnu-sed", "gawk", "wget", "git"])
    except subprocess.CalledProcessError:
        print("Fehler beim Installieren der Abhängigkeiten. Prüfe Homebrew-Installation.")
        sys.exit(1)

def create_qemu_image(image_name, image_size="100M"):
    """Erstellt ein QEMU-Image."""
    run_command(["qemu-img", "create", "-f", "qcow2", image_name, image_size])

def format_qemu_image(image_name):
    """Formatiert das QEMU-Image als ext4-Dateisystem."""
    run_command(["mkfs.ext4", "-F", image_name])

def mount_image(image_name, mount_point):
    """Mountet das QEMU-Image an ein temporäres Verzeichnis."""
    if not os.path.exists(mount_point):
        os.makedirs(mount_point)
    run_command(["sudo", "mount", "-o", "loop", image_name, mount_point])

def unmount_image(mount_point):
    """Unmountet das QEMU-Image vom temporären Verzeichnis."""
    run_command(["sudo", "umount", mount_point])

def build_busybox(arch):
    """Lädt und kompiliert BusyBox, um ein minimalistisches Root-Dateisystem zu erstellen."""
    busybox_url = "https://busybox.net/downloads/busybox-1.34.1.tar.bz2"
    busybox_tar = "busybox-1.34.1.tar.bz2"
    busybox_dir = "busybox-1.34.1"

    run_command(["wget", busybox_url])
    run_command(["tar", "-xvf", busybox_tar])

    os.chdir(busybox_dir)
    run_command(["make", "defconfig"])
    run_command(["make", f"ARCH={arch}", "install"])
    
    os.chdir("..")
    return os.path.join(busybox_dir, "_install")

def setup_rootfs(rootfs_dir, mount_point, hprocs_path):
    """Kopiert BusyBox-Installationsdateien und fügt die hprocs-Datei hinzu."""
    print(f"Kopiere BusyBox in das Root-Dateisystem: {mount_point}")
    shutil.copytree(rootfs_dir, mount_point, dirs_exist_ok=True)

    # hprocs Datei in das Root-Dateisystem kopieren
    target_hprocs = os.path.join(mount_point, "init")
    print(f"Kopiere hprocs nach {target_hprocs} und setze sie als Init-Prozess.")
    shutil.copy(hprocs_path, target_hprocs)

    # Setze die Berechtigungen korrekt
    run_command(["chmod", "+x", target_hprocs])

def build_kernel(arch, cross_compile, kernel_version):
    """Lädt den Linux-Kernel herunter und kompiliert ihn."""
    kernel_tar = f"linux-{kernel_version}.tar.xz"
    kernel_url = f"https://cdn.kernel.org/pub/linux/kernel/v6.x/{kernel_tar}"

    run_command(["wget", kernel_url])
    run_command(["tar", "-xvf", kernel_tar])
    os.chdir(f"linux-{kernel_version}")

    # Kernel-Konfiguration und Kompilierung
    run_command(["make", "defconfig", f"ARCH={arch}"])
    run_command(["make", f"ARCH={arch}", f"CROSS_COMPILE={cross_compile}", "all", "-j4"])

def clone_and_build_external_repo(repo_url, repo_dir):
    """Klonen eines externen Repositories und dessen Build-Prozess."""
    if not os.path.exists(repo_dir):
        print(f"Klonen des Repositories von {repo_url} in {repo_dir}")
        run_command(["git", "clone", repo_url, repo_dir])
    else:
        print(f"Repository {repo_dir} existiert bereits. Aktualisiere es...")
        run_command(["git", "pull"], cwd=repo_dir)

    # Wechsel in das Repository und baue es
    os.chdir(repo_dir)
    run_command(["make"])

    # Suche nach der hprocs-Datei
    hprocs_path = os.path.join(repo_dir, "hprocs")
    if not os.path.exists(hprocs_path):
        print(f"hprocs-Datei nicht gefunden im Verzeichnis {repo_dir}.")
        sys.exit(1)
    return hprocs_path

def main():
    # Architektur und Compiler erkennen
    arch, cross_compile = detect_architecture()
    print(f"Architektur erkannt: {arch}")

    # Installiere Abhängigkeiten
    install_dependencies()

    # Kernel bauen
    kernel_version = "6.5"
    build_kernel(arch, cross_compile, kernel_version)

    # Externes Repository klonen und bauen
    repo_url = "https://github.com/beispiel/external-repo.git"  # Passe diese URL an
    repo_dir = "external-repo"
    hprocs_path = clone_and_build_external_repo(repo_url, repo_dir)

    # QEMU-Image erstellen
    image_name = "qemu_image.img"
    create_qemu_image(image_name)
    format_qemu_image(image_name)

    # Mount das QEMU-Image
    mount_point = "/mnt/qemu_image"
    mount_image(image_name, mount_point)

    # BusyBox bauen und Root-Dateisystem einrichten
    rootfs_dir = build_busybox(arch)
    setup_rootfs(rootfs_dir, mount_point, hprocs_path)

    # Unmount das QEMU-Image
    unmount_image(mount_point)

    print(f"QEMU-Image {image_name} erfolgreich erstellt und konfiguriert!")

if __name__ == "__main__":
    main()