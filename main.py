import os
import sys
import shutil
import json
import webbrowser
import subprocess
import psutil

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer

import minecraft_launcher_lib


# === PATH HELPERS ===

def get_appdata_path():
    return os.path.join(os.getenv("APPDATA"), "BarrieLauncher")

def resource_path(relative_path):
    """Get absolute path to bundled asset (for PyInstaller compatibility)"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


# === MINECRAFT LAUNCHER LOGIC ===

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
        "uuid": "12345678-1234-1234-1234-123456789abc",
        "token": "fake-token"
    }

    minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
    minecraft_launcher_lib.install.install_minecraft_version(version, minecraft_directory)
    command = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_directory, options)

    process = subprocess.Popen(command)
    process.wait()

    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid:
                if "barrie-launcher" in ' '.join(proc.info['cmdline']).lower():
                    proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


# === MAIN UI ===

class BarrieLauncher(QWidget):
    def __init__(self):
        super().__init__()

        # === AppData Paths ===
        self.appdata_dir = get_appdata_path()
        self.assets_dir = os.path.join(self.appdata_dir, "assets")
        self.ads_dir = os.path.join(self.appdata_dir, "images")
        self.icon_path = os.path.join(self.assets_dir, "logo.ico")

        self.ensure_assets_exist()

        self.setWindowTitle("Barrie Launcher")
        self.setFixedSize(900, 520)
        self.setWindowIcon(QIcon(self.icon_path))
        self.setStyleSheet("background-color: #2c2c2c; color: white; font-family: 'Segoe UI';")

        main_layout = QHBoxLayout(self)

        # === Sidebar ===
        sidebar = QVBoxLayout()
        sidebar.setAlignment(Qt.AlignTop)

        logo = QLabel()
        logo_image = QPixmap(os.path.join(self.assets_dir, "logo.png"))
        if not logo_image.isNull():
            logo.setPixmap(logo_image.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        sidebar.addWidget(logo)

        for name, icon, url in [
            ("GitHub", "💻", "https://github.com"),
            ("YouTube", "▶️", "https://youtube.com"),
            ("Instagram", "📸", "https://instagram.com")
        ]:
            btn = QPushButton(f"{icon} {name}")
            btn.setStyleSheet("background-color: #444; padding: 10px;")
            btn.clicked.connect(lambda _, link=url: webbrowser.open(link))
            sidebar.addWidget(btn)

        sidebar_frame = QFrame()
        sidebar_frame.setLayout(sidebar)
        sidebar_frame.setFixedWidth(160)
        sidebar_frame.setStyleSheet("background-color: #1a1a1a;")
        main_layout.addWidget(sidebar_frame)

        # === Main Area ===
        ui_layout = QVBoxLayout()

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your Minecraft username")
        self.username_input.setFixedWidth(300)
        top_bar.addWidget(self.username_input)
        top_bar.addStretch()
        ui_layout.addLayout(top_bar)

        self.ad_label = QLabel()
        self.ad_label.setFixedHeight(220)
        self.ad_label.setAlignment(Qt.AlignCenter)
        self.ad_label.setStyleSheet("background-color: #111; border: 1px solid #333;")
        ui_layout.addWidget(self.ad_label)

        self.ads = []
        self.ad_index = 0
        if os.path.exists(self.ads_dir):
            for file in sorted(os.listdir(self.ads_dir)):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    self.ads.append(os.path.join(self.ads_dir, file))

        self.update_ad()
        self.ad_timer = QTimer()
        self.ad_timer.timeout.connect(self.update_ad)
        self.ad_timer.start(3000)

        bottom_bar = QHBoxLayout()
        self.version_dropdown = QComboBox()
        self.version_map = {}
        for label, version_id in get_available_versions():
            self.version_dropdown.addItem(label)
            self.version_map[label] = version_id
        self.version_dropdown.setFixedWidth(160)

        self.start_btn = QPushButton("START")
        self.start_btn.setFixedWidth(160)
        self.start_btn.setStyleSheet("background-color: #6ab04c; font-size: 16px; padding: 10px; font-weight: bold;")
        self.start_btn.clicked.connect(self.launch_game)

        bottom_bar.addWidget(self.version_dropdown)
        bottom_bar.addWidget(self.start_btn)
        bottom_bar.addStretch()
        ui_layout.addLayout(bottom_bar)

        footer = QLabel("🔧 Made by @nextgenmilo | For Educational Purposes Only.")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 10px; color: gray; margin-top: 10px;")
        ui_layout.addWidget(footer)

        main_layout.addLayout(ui_layout)

    def update_ad(self):
        if not self.ads:
            self.ad_label.setText("No ads found.")
            return
        pixmap = QPixmap(self.ads[self.ad_index])
        if not pixmap.isNull():
            self.ad_label.setPixmap(pixmap.scaled(self.ad_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.ad_index = (self.ad_index + 1) % len(self.ads)

    def launch_game(self):
        username = self.username_input.text()
        selected_label = self.version_dropdown.currentText()
        version_id = self.version_map.get(selected_label)

        if not username:
            print("Username is required.")
            return

        self.hide()
        try:
            launch_minecraft(username, version_id)
        except Exception as e:
            print(f"Launch failed: {e}")
        finally:
            self.show()

    def ensure_assets_exist(self):
        os.makedirs(self.assets_dir, exist_ok=True)
        os.makedirs(self.ads_dir, exist_ok=True)

        # === Copy logo files
        for logo in ["logo.png", "logo.ico"]:
            dst = os.path.join(self.assets_dir, logo)
            if not os.path.exists(dst):
                src = resource_path(f"assets/{logo}")
                if os.path.exists(src):
                    shutil.copy(src, dst)

        # === Copy default ad images if none exist
        if not any(f.lower().endswith((".png", ".jpg", ".jpeg")) for f in os.listdir(self.ads_dir)):
            ads_folder = resource_path("images")
            if os.path.exists(ads_folder):
                for file in os.listdir(ads_folder):
                    if file.lower().endswith((".png", ".jpg", ".jpeg")):
                        shutil.copy(os.path.join(ads_folder, file), os.path.join(self.ads_dir, file))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = BarrieLauncher()
    launcher.show()
    sys.exit(app.exec())
