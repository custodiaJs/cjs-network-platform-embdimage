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
        run_command(["apt-get", "update"])
        run_command(["apt-get", "install", "-y", "qemu", "gcc", "make", "wget", "git", "libncurses-dev", "bison", "flex"])
    except subprocess.CalledProcessError:
        print("Fehler beim Installieren der Abhängigkeiten. Prüfe deine Installation.")
        sys.exit(1)

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

def setup_rootfs(rootfs_dir, hprocs_path):
    """Kopiert BusyBox-Installationsdateien und fügt die hprocs-Datei hinzu."""
    print(f"Kopiere BusyBox in das Root-Dateisystem: {rootfs_dir}")
    shutil.copytree(rootfs_dir, "/target-rootfs", dirs_exist_ok=True)

    # hprocs Datei in das Root-Dateisystem kopieren
    target_hprocs = os.path.join("/target-rootfs", "init")
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

    # BusyBox bauen und Root-Dateisystem einrichten
    rootfs_dir = build_busybox(arch)
    setup_rootfs(rootfs_dir, hprocs_path)

    print(f"System erfolgreich eingerichtet!")

if __name__ == "__main__":
    main()