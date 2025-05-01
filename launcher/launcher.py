import minecraft_launcher_lib
import os
import subprocess
import psutil

def get_available_versions():
    versions = minecraft_launcher_lib.utils.get_version_list()
    labeled_versions = []

    type_labels = {
        "release": "Release",
        "snapshot": "Snapshot",
        "old_beta": "Beta",
        "old_alpha": "Alpha"
    }

    for v in versions:
        v_type = v["type"]
        if v_type in type_labels:
            label = f"{type_labels[v_type]} - {v['id']}"
            labeled_versions.append((label, v["id"]))

    return labeled_versions

def launch_minecraft(username, version):
    options = {
        "username": username,
        "uuid": "12345678-1234-1234-1234-123456789abc",  # Fake UUID
        "token": "fake-token"
    }

    minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()

    # Download the version if not already installed
    minecraft_launcher_lib.install.install_minecraft_version(version, minecraft_directory)

    # Create launch command
    command = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_directory, options)

    # ✅ Launch Minecraft with subprocess (non-blocking)
    process = subprocess.Popen(command)

    # 🧼 Wait for Minecraft to close
    process.wait()

    # 🧼 Clean up any leftover launcher processes
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid:
                if "barrie-launcher" in ' '.join(proc.info['cmdline']).lower():
                    proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
