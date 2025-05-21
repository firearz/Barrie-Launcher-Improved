import os
import sys
import shutil
import json
import webbrowser
import subprocess
import psutil
import requests
import tempfile
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QDialog, QListView, QAbstractItemView, QCheckBox, QMessageBox,
    QTabWidget, QSlider
)

from PySide6.QtGui import QPixmap, QIcon, QStandardItemModel, QStandardItem, QFont
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter
import minecraft_launcher_lib
from PySide6.QtGui import QPainter, QPixmap, QColor, QImage
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QPushButton, QVBoxLayout, QFileDialog, QGraphicsRectItem, QGraphicsItem
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QMouseEvent, QBrush
from PySide6.QtCore import QRectF, Qt, QPointF
def get_appdata_path():
    return os.path.join(os.getenv("APPDATA"), "BarrieLauncher")

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

VERSION_FILE = os.path.join(get_appdata_path(), "versions.txt")
VERSION_API = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
class CropBox(QGraphicsRectItem):
    def __init__(self, rect):
        super().__init__(rect)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setPen(QPen(Qt.green, 2))
        self.setBrush(QBrush(QColor(0, 255, 0, 40)))

SETTINGS_FILE = os.path.join(get_appdata_path(), "settings.json")

def save_settings(username, version_id, ram_mb=None):
    data = {"username": username, "version_id": version_id}
    if ram_mb is not None:
        data["ram_mb"] = ram_mb

    os.makedirs(get_appdata_path(), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_available_versions(offline=False):
    versions = []
    try:
        if offline:
            raise Exception("Forced offline")
        mc_versions = minecraft_launcher_lib.utils.get_version_list()
        with open(VERSION_FILE, "w") as f:
            for v in mc_versions:
                f.write(v["id"] + "\n")
    except Exception as e:
        print("Offline or error fetching versions:", e)
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r") as f:
                version_ids = f.read().splitlines()
            mc_versions = [{"id": vid, "type": "release"} for vid in version_ids]
        else:
            return [("Offline: No cached versions", "")]
    type_labels = {
        "release": "Release",
        "snapshot": "Snapshot",
        "old_beta": "Beta",
        "old_alpha": "Alpha"
    }
    labeled_versions = []
    for v in mc_versions:
        label = f"{type_labels.get(v.get('type', 'release'), 'Other')} - {v['id']}"
        labeled_versions.append((label, v["id"]))
    return labeled_versions

def get_installed_fabric_versions():
    fabric_versions = []
    versions_dir = os.path.join(minecraft_launcher_lib.utils.get_minecraft_directory(), "versions")
    if os.path.exists(versions_dir):
        for folder_name in os.listdir(versions_dir):
            if "fabric-loader" in folder_name:
                fabric_versions.append(folder_name)
    return fabric_versions

from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QMouseEvent
from PySide6.QtCore import Qt, QRect

class SettingsDialog(QDialog):


    def save_and_close(self):
        value = self.ram_slider.value()             # Value in GB
        ram_mb = value * 1024                       # Convert to MB

    # Load existing settings
        settings = load_settings()

    # Update only ram_mb, leave username and version_id unchanged
        save_settings(
            settings.get("username", ""), 
            settings.get("version_id", ""), 
            ram_mb
        )

        self.accept()  # Close the dialog


    def update_ram_label(self, value):
        self.ram_label.setText(f"Allocated RAM: {value} GB")


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Launcher Settings")
        self.setMinimumSize(400, 300)

        tabs = QTabWidget()

        # === General Tab ===
        general_tab = QWidget()
        general_layout = QVBoxLayout()

        self.ram_slider = QSlider(Qt.Horizontal)
        self.ram_slider.setMinimum(1)      # 1 GB
        self.ram_slider.setMaximum(16)     # 16 GB
        self.ram_slider.setSingleStep(1)

# Set RAM from saved settings
        settings = load_settings()
        ram_mb = settings.get("ram_mb", 2048)
        slider_value = ram_mb // 1024      # Direct GB
        self.ram_slider.setValue(slider_value)


        self.ram_label = QLabel()
        self.update_ram_label(self.ram_slider.value())
        self.ram_slider.valueChanged.connect(self.update_ram_label)

        general_layout.addWidget(self.ram_label)
        general_layout.addWidget(self.ram_slider)
        general_tab.setLayout(general_layout)

        # === Tabs ===
        tabs.addTab(general_tab, "General")
        tabs.addTab(QWidget(), "Game Settings")
        tabs.addTab(QWidget(), "Mods")
        tabs.addTab(QWidget(), "Advanced")

        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_and_close)

        layout = QVBoxLayout()
        layout.addWidget(tabs)
        layout.addWidget(save_button)
        self.setLayout(layout)


class CropDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crop Profile Photo")
        self.setMinimumSize(600, 600)

        self.image = QPixmap(image_path)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.pixmap_item = QGraphicsPixmapItem(self.image)
        self.scene.addItem(self.pixmap_item)

        # Fit image to scene
        img_rect = QRectF(self.image.rect())
        self.scene.setSceneRect(img_rect)
        self.view.fitInView(img_rect, Qt.KeepAspectRatio)

        # Add a crop box at center
        box_size = min(self.image.width(), self.image.height()) // 2
        box_x = (self.image.width() - box_size) // 2
        box_y = (self.image.height() - box_size) // 2
        self.crop_box = CropBox(QRectF(box_x, box_y, box_size, box_size))
        self.scene.addItem(self.crop_box)

        confirm_btn = QPushButton("Crop & Save")
        confirm_btn.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(confirm_btn)
        self.setLayout(layout)

    def get_cropped_pixmap(self):
        rect = self.crop_box.rect().toRect()
        img_rect = rect.intersected(self.image.rect())
        cropped = self.image.copy(img_rect)

        # Resize to standard square size (e.g., 256x256)
        return cropped.scaled(256, 256, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
class DownloadedVersionSelector(QDialog):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Downloaded Version")
        self.setFixedSize(400, 350)
        self.username = username
        self.parent_window = parent

        layout = QVBoxLayout(self)

        self.edition_dropdown = QComboBox()
        self.edition_dropdown.addItems(["Vanilla", "Fabric", "Forge"])
        layout.addWidget(self.edition_dropdown)

        self.model = QStandardItemModel(self)
        self.version_list = QListView()
        self.version_list.setModel(self.model)
        self.version_list.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.version_list)

        self.launch_button = QPushButton("Launch")
        self.launch_button.clicked.connect(self.launch_selected)
        layout.addWidget(self.launch_button)

        self.edition_dropdown.currentTextChanged.connect(self.update_versions)
        self.update_versions()

    def update_versions(self):
        self.model.clear()
        edition = self.edition_dropdown.currentText().lower()
        versions_dir = os.path.join(minecraft_launcher_lib.utils.get_minecraft_directory(), "versions")

        for folder in os.listdir(versions_dir):
            if edition == "vanilla" and not ("fabric-loader" in folder or "forge" in folder):
                self.model.appendRow(QStandardItem(folder))
            elif edition == "fabric" and "fabric-loader" in folder:
                self.model.appendRow(QStandardItem(folder))
            elif edition == "forge" and "forge" in folder:
                self.model.appendRow(QStandardItem(folder))

    def launch_selected(self):
        selected = self.version_list.selectedIndexes()
        if selected:
            version = selected[0].data()
            print(f"Launching: {version}")
            self.accept()
            minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
            options = {
                "username": self.username,
                "uuid": "12345678-1234-1234-1234-123456789abc",
                "token": "faketoken"
            }
            try:
                command = minecraft_launcher_lib.command.get_minecraft_command(
                    version, minecraft_directory, options
                )
                self.parent_window.hide()
                process = subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
                process.wait()
                self.parent_window.show()
            except Exception as e:
                print(f"Failed to launch selected version: {e}")
        else:
            QMessageBox.warning(self, "No Version Selected", "Please select a version to launch.")

class FabricVersionSelector(QDialog):
    def __init__(self, fabric_versions, username, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Fabric Version")
        self.setFixedSize(400, 300)
        self.username = username
        self.parent_window = parent

        layout = QVBoxLayout()
        self.model = QStandardItemModel(self)
        for version in fabric_versions:
            item = QStandardItem(version)
            self.model.appendRow(item)
        self.version_list = QListView()
        self.version_list.setModel(self.model)
        self.version_list.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.version_list)
        self.launch_button = QPushButton("Launch")
        self.launch_button.clicked.connect(self.launch_fabric)
        layout.addWidget(self.launch_button)
        self.setLayout(layout)

    def launch_fabric(self):
        selected_index = self.version_list.selectedIndexes()
        if selected_index:
            selected_version = selected_index[0].data()
            print(f"Launching Fabric with version: {selected_version}")
            self.accept()
            minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
            options = {
                "username": self.username,
                "uuid": "12345678-1234-1234-1234-123456789abc",
                "token": "faketoken"
            }
            try:
                command = minecraft_launcher_lib.command.get_minecraft_command(
                    selected_version, minecraft_directory, options
                )
                env = os.environ.copy()
                env["FABRIC_MODS_DIR"] = os.path.join(minecraft_directory, "mods", selected_version)
                self.parent_window.hide()
                process = subprocess.Popen(command, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
                process.wait()
                self.parent_window.show()
            except Exception as e:
                print(f"Error launching Fabric: {e}")
        else:
            print("No Fabric version selected.")
        self.install_customskinloader(selected_version)
def launch_minecraft(username, version, mode="Vanilla", offline_mode=False):
    options = {
        "username": username,
        "uuid": "12345678-1234-1234-1234-123456789abc",
        "token": "faketoken"
    }
    minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
    if mode.lower() == "fabric":
        try:
            print(f"Installing Fabric for Minecraft version: {version}")
            minecraft_launcher_lib.fabric.install_fabric(version, minecraft_directory)
            fabric_versions = get_installed_fabric_versions()
            fabric_selector = FabricVersionSelector(fabric_versions, username, parent=window)
            fabric_selector.exec_()
            return
        except Exception as e:
            print(f"Error handling Fabric installation: {e}")
            return
    elif mode.lower() == "forge":
        try:
            print(f"Installing Forge for Minecraft version: {version}")
            minecraft_launcher_lib.forge.install_forge(version, minecraft_directory)
            command = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_directory, options)
            window.hide()
            process = subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
            process.wait()
            window.show()
        except Exception as e:
            print(f"Error installing Forge: {e}")
            return
    else:
        if not offline_mode:
            minecraft_launcher_lib.install.install_minecraft_version(version, minecraft_directory)
        command = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_directory, options)
        window.hide()
        process = subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
        process.wait()
        window.show()

def get_instance_path(version_name):
    base_dir = os.path.join(minecraft_launcher_lib.utils.get_minecraft_directory(), "instances")
    return os.path.join(base_dir, version_name)
class SkinDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fetch Skin by UUID")
        self.setFixedSize(300, 400)

        layout = QVBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter UUID")
        layout.addWidget(self.input)

        self.skin_label = QLabel("Skin Preview")
        self.skin_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.skin_label)

        fetch_button = QPushButton("Fetch Skin")
        fetch_button.clicked.connect(self.fetch_skin)
        layout.addWidget(fetch_button)

        self.setLayout(layout)

    def fetch_skin(self):
        uuid = self.input.text().strip()
        if not uuid:
            QMessageBox.warning(self, "Missing UUID", "Please enter a UUID.")
            return
        try:
            url = f"https://crafatar.com/skins/{uuid}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                tmp_file = os.path.join(tempfile.gettempdir(), f"{uuid}.png")
                with open(tmp_file, "wb") as f:
                    f.write(response.content)
                pixmap = QPixmap(tmp_file).scaled(100, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.skin_label.setPixmap(pixmap)

                self.selected_uuid = uuid  # Save UUID
                self.accept()  # Close dialog and return to launcher
            else:
                QMessageBox.warning(self, "Not Found", "Could not fetch skin. Check UUID.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch skin:\n{e}")
class CustomSkinLoaderDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Set Custom Skin (Offline)")
            self.setFixedSize(300, 150)

            layout = QVBoxLayout()

            self.input = QLineEdit()
            self.input.setPlaceholderText("Enter Minecraft username")
            layout.addWidget(self.input)

            self.ok_button = QPushButton("Download Skin")
            self.ok_button.clicked.connect(self.download_skin)
            layout.addWidget(self.ok_button)

            self.setLayout(layout)
            
        def download_skin(self):
            username = self.input.text().strip()
            if not username:
                QMessageBox.warning(self, "Missing Username", "Please enter a username.")
                return

            try:
                # Get skin from Crafatar
                skin_url = f"https://crafatar.com/skins/{username}"
                r = requests.get(skin_url, timeout=10)
                if r.status_code != 200:
                    QMessageBox.warning(self, "Skin Error", "Skin not found.")
                    return

                # Save to CustomSkinLoader config
                mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
                csl_dir = os.path.join(mc_dir, "CustomSkinLoader", "Skins")
                os.makedirs(csl_dir, exist_ok=True)
                skin_path = os.path.join(csl_dir, f"{username}.png")
                with open(skin_path, "wb") as f:
                    f.write(r.content)

                QMessageBox.information(self, "Skin Set", f"Skin for '{username}' installed.")
                self.accept()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to download skin:\n{e}")

class SkinRedirectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Map Skin from One Username to Another")
        self.setFixedSize(350, 200)

        layout = QVBoxLayout()

        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Skin from (username1)")
        layout.addWidget(self.source_input)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Apply to (username2)")
        layout.addWidget(self.target_input)

        self.ok_button = QPushButton("Apply")
        self.ok_button.clicked.connect(self.download_and_map_skin)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def download_and_map_skin(self):
        username1 = self.source_input.text().strip()
        username2 = self.target_input.text().strip()

        if not username1 or not username2:
            QMessageBox.warning(self, "Input Error", "Both usernames are required.")
            return

        try:
            skin_url = f"https://crafatar.com/skins/{username1}"
            r = requests.get(skin_url, timeout=10)
            if r.status_code != 200:
                QMessageBox.warning(self, "Skin Error", f"Could not get skin for {username1}")
                return

            mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
            skin_dir = os.path.join(mc_dir, "CustomSkinLoader", "Skins")
            os.makedirs(skin_dir, exist_ok=True)

            skin_path = os.path.join(skin_dir, f"{username2}.png")
            with open(skin_path, "wb") as f:
                f.write(r.content)

            QMessageBox.information(self, "Success", f"{username2} will now use {username1}'s skin.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Download failed: {e}")


class BarrieLauncher(QWidget):
    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.exec_()


    def install_legacy_forge(self, version_id):
        mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
        installer_url = "https://maven.minecraftforge.net/net/minecraftforge/forge/1.7.10-10.13.4.1614-1.7.10/forge-1.7.10-10.13.4.1614-1.7.10-installer.jar"
        installer_path = os.path.join(get_appdata_path(), "forge_installer_1.7.10.jar")
        version_folder = os.path.join(mc_dir, "versions", version_id)

        try:
        # Download installer
            if not os.path.exists(installer_path):
                r = requests.get(installer_url, stream=True, timeout=30)
                if r.status_code == 200:
                    with open(installer_path, "wb") as f:
                        shutil.copyfileobj(r.raw, f)
                    print("Forge 1.7.10 installer downloaded.")
                else:
                    QMessageBox.warning(self, "Download Failed", "Could not download Forge 1.7.10 installer.")
                    return

        # Check if Java is installed
            try:
                subprocess.run(["java", "-version"], capture_output=True, check=True)
            except Exception:
                QMessageBox.critical(self, "Java Missing", "Java is required to install Forge 1.7.10. Please install Java and add it to PATH.")
                return

        # Run installer
            subprocess.run(["java", "-jar", installer_path, "--installClient"], cwd=mc_dir, creationflags=subprocess.CREATE_NO_WINDOW)

        # Check if the version folder was created
            if not os.path.exists(version_folder):
                QMessageBox.warning(self, "Installation Failed", f"Forge version folder '{version_id}' was not created.")
                return

        # Ensure required files are there
            jar_path = os.path.join(version_folder, f"{version_id}.jar")
            json_path = os.path.join(version_folder, f"{version_id}.json")

            if not os.path.exists(jar_path) or not os.path.exists(json_path):
            # Copy vanilla jar if missing
                base_version = "1.7.10"
                base_jar = os.path.join(mc_dir, "versions", base_version, f"{base_version}.jar")
                if os.path.exists(base_jar):
                    shutil.copy(base_jar, jar_path)
                    print("Base jar copied to Forge folder.")
                else:
                    QMessageBox.warning(self, "Missing Base Version", "Minecraft 1.7.10 is not installed. Please install it first.")
                    return

        # Generate launcher profile
            self.ensure_launcher_profile_exists(version_id)

        # Launch
            options = {
                "username": self.username_input.text().strip(),
                "uuid": "12345678-1234-1234-1234-123456789abc",
                "token": "faketoken"
            }
            command = minecraft_launcher_lib.command.get_minecraft_command(version_id, mc_dir, options)
            self.hide()
            subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW).wait()
            self.show()

        except Exception as e:
            QMessageBox.critical(self, "Forge Install Failed", f"Failed to install Forge 1.7.10:\n{e}")


    def load_profile_photo(self):
        profile_img_path = os.path.join(get_appdata_path(), "profile.png")
        if not os.path.exists(profile_img_path):
            profile_img_path = os.path.join(self.assets_dir, "logo.png")

        pixmap = QPixmap(profile_img_path)
        if pixmap.isNull():
            return

        size = min(pixmap.width(), pixmap.height())
        rect = QRect(
            (pixmap.width() - size) // 2,
            (pixmap.height() - size) // 2,
            size,
            size
        )
        cropped = pixmap.copy(rect).scaled(80, 80, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    # Create circular mask
        mask = QPixmap(80, 80)
        mask.fill(Qt.transparent)

        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.white)
        painter.drawEllipse(0, 0, 80, 80)
        painter.end()

        cropped.setMask(mask.createMaskFromColor(Qt.transparent, Qt.MaskInColor))
        self.profile_label.setPixmap(cropped)

    def change_profile_photo(self, event):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Profile Picture", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            crop_dialog = CropDialog(file_path, self)
            if crop_dialog.exec() == QDialog.Accepted:
                cropped = crop_dialog.get_cropped_pixmap()
                dest_path = os.path.join(get_appdata_path(), "profile.png")
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                cropped.save(dest_path, "PNG")
                self.load_profile_photo()

    

    def auto_download_skin(self, username):
        try:
            skin_url = f"https://crafatar.com/skins/{username}"
            response = requests.get(skin_url, timeout=10)
            if response.status_code == 200:
                mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
                csl_dir = os.path.join(mc_dir, "CustomSkinLoader", "Skins")
                os.makedirs(csl_dir, exist_ok=True)
                skin_path = os.path.join(csl_dir, f"{username}.png")
                with open(skin_path, "wb") as f:
                    f.write(response.content)
                print(f"Skin downloaded for {username}")
            else:
                print(f"Skin not found for {username}")
        except Exception as e:
            print(f"Failed to fetch skin for {username}: {e}")

    
    def fix_forge_missing_jar(self, version_id):
        mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
        forge_dir = os.path.join(mc_dir, "versions", version_id)
        forge_jar = os.path.join(forge_dir, f"{version_id}.jar")

        if not os.path.exists(forge_jar):
            # Extract the base version from Forge string (e.g., "1.7.10-Forge10.13.4.1614-1.7.10" → "1.7.10")
            base_version = version_id.split('-')[0]
            vanilla_jar = os.path.join(mc_dir, "versions", base_version, f"{base_version}.jar")

            if os.path.exists(vanilla_jar):
                os.makedirs(forge_dir, exist_ok=True)
                shutil.copy(vanilla_jar, forge_jar)
                print(f"Copied {base_version}.jar to Forge folder as {version_id}.jar")
            else:
                QMessageBox.warning(self, "Missing base version",
                                f"The base version {base_version} is not installed. Please install it first using your launcher.")

    
    def ensure_launcher_profile_exists(self, version_id):
        mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
        profile_path = os.path.join(mc_dir, "launcher_profiles.json")

    # Try to load existing JSON if valid
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r") as f:
                    data = json.load(f)
                return  # File is valid, no need to change
            except json.JSONDecodeError:
                print("Corrupted launcher_profiles.json, regenerating...")

    # Create a basic valid launcher_profiles.json
        data = {
            "profiles": {
                "forge": {
                    "name": "Forge",
                    "lastVersionId": version_id,
                    "type": "custom"
                }
            },
            "selectedProfile": "forge",
            "clientToken": "12345678-1234-1234-1234-123456789abc",
            "launcherVersion": {
                "name": "custom-launcher",
                "format": 21
            }
        }

        with open(profile_path, "w") as f:
            json.dump(data, f, indent=4)
        print("Created default launcher_profiles.json for Forge.")


    def install_and_launch_forge(self, username, version_id):
        minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        options = {
            "username": username,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "token": "faketoken"
        }

        try:
            print(f"Installing Forge for Minecraft version: {version_id}")
            minecraft_launcher_lib.forge.install_forge(version_id, minecraft_directory)
        except AttributeError as e:
            if "install_forge" in str(e) and "1.7.10" in version_id:
                self.install_legacy_forge(version_id)
                return
        
            else:
                QMessageBox.warning(self, "Unsupported Forge", f"Automatic installation not supported for Forge {version_id}. Please install it manually from the Forge website.")
                self.ensure_launcher_profile_exists(version_id)
            return

        self.ensure_launcher_profile_exists(version_id)
        self.fix_forge_missing_jar(version_id)

        try:
            command = minecraft_launcher_lib.command.get_minecraft_command(version_id, minecraft_directory, options)
            self.hide()
            process = subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
            process.wait()
            self.show()
        except Exception as e:
            print(f"Failed to launch Forge: {e}")

            


    def __init__(self):
        self.custom_uuid = None  # Will be set by the Skin dialog
        self.selected_uuid = None
        
        super().__init__()
        self.appdata_dir = get_appdata_path()
        self.assets_dir = os.path.join(self.appdata_dir, "assets")
        self.ads_dir = os.path.join(self.appdata_dir, "images")
        self.icon_path = os.path.join(self.assets_dir, "logo.ico")
        self.ensure_assets_exist()
        self.setWindowTitle("Barrie Launcher")
        self.setWindowIcon(QIcon(self.icon_path))
        self.setMinimumSize(900, 520)
        self.setStyleSheet(self.load_styles())
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        # Sidebar
        sidebar = QVBoxLayout()
        sidebar.setAlignment(Qt.AlignTop)
        sidebar.setSpacing(20)
        self.profile_label = QLabel()
        self.profile_label.setFixedSize(80, 80)
        self.profile_label.setAlignment(Qt.AlignCenter)
        self.profile_label.setStyleSheet("""
            QLabel {
                border-radius: 40px;
                border: 2px solid #3b5cff;
                background-color: #1a1d29;
            }
        """)
        self.profile_label.mousePressEvent = self.change_profile_photo
        self.load_profile_photo()
        sidebar.addWidget(self.profile_label, alignment=Qt.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your Minecraft username")
        # Load stored settings
        settings = load_settings()
        if "username" in settings:
            self.username_input.setText(settings["username"])

# Later: we'll apply the version_id as well, once dropdown is filled
        self.pending_version_id = settings.get("version_id")

        sidebar.addWidget(self.username_input)
        # Replace Offline Mode with Fabric Mode checkbox.
        self.downloaded_checkbox = QCheckBox("Downloaded Versions")
        sidebar.addWidget(self.downloaded_checkbox)
        # sidebar.addWidget(self.fabric_mode_checkbox)
        social_links = [
            ("GitHub", "github.png", "https://github.com/firearz/Barrie-Launcher-Improved"),
            ("YouTube", "youtube.png", "https://www.youtube.com/@nextgenmilo?sub_confirmation=1"),
            ("Instagram", "instagram.png", "https://instagram.com/nextgenmilo")
        ]
        
        


        

        for name, icon_file, url in social_links:
            btn = QPushButton(name)
            icon_path = os.path.join(self.assets_dir, icon_file)
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
            btn.clicked.connect(lambda _, link=url: webbrowser.open(link))
            sidebar.addWidget(btn)
        sidebar_frame = QFrame()
        sidebar_frame.setLayout(sidebar)
        sidebar_frame.setFixedWidth(200)
        sidebar_frame.setStyleSheet("background-color: #0d0f1a; border-right: 1px solid #1f2233;")
        main_layout.addWidget(sidebar_frame)
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        title = QLabel("Barrie Launcher")
        # Settings button
        settings_button = QPushButton("⚙")
        settings_button.setFixedSize(30, 30)
        settings_button.setStyleSheet("font-size: 16px; font-weight: bold;")
        settings_button.clicked.connect(self.open_settings_dialog)

# Add settings button to a horizontal layout
        header_layout = QHBoxLayout()
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(settings_button)
        content_layout.addLayout(header_layout)

        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        content_layout.addWidget(title)
        tools_layout = QHBoxLayout()
        mods_button = QPushButton("Mods")
        mods_button.clicked.connect(self.open_mods_menu)
        rp_button = QPushButton("Resource Packs")
        rp_button.clicked.connect(self.open_resourcepacks_folder)
        sodium_button = QPushButton("Instant Sodium")
        sodium_button.clicked.connect(self.open_sodium_installer)
        tools_layout.addWidget(mods_button)
        tools_layout.addWidget(rp_button)
        tools_layout.addWidget(sodium_button)
        content_layout.addLayout(tools_layout)
        edition_label = QLabel("Select Minecraft Edition")
        edition_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(edition_label)
        self.edition_dropdown = QComboBox()
        self.edition_dropdown.addItems(["Vanilla", "Fabric", "Forge"])
        content_layout.addWidget(self.edition_dropdown)
        version_label = QLabel("Select Minecraft Version")
        version_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(version_label)
        self.version_dropdown = QComboBox()
        self.versions = get_available_versions()
        for label, version in self.versions:
            self.version_dropdown.addItem(label, version)
        # Apply stored version selection
        if self.pending_version_id:
            index = self.version_dropdown.findData(self.pending_version_id)
            if index != -1:
                self.version_dropdown.setCurrentIndex(index)

        content_layout.addWidget(self.version_dropdown)
        self.play_button = QPushButton("Play")
        self.play_button.setObjectName("playButton")
        self.play_button.clicked.connect(self.on_play_clicked)
        content_layout.addWidget(self.play_button)
        footer = QLabel("© 2025 Barrie Launcher | Powered by Minecraft Launcher Lib")
        footer.setAlignment(Qt.AlignCenter)
        footer.setObjectName("footer")
        content_layout.addWidget(footer)
        main_layout.addLayout(content_layout)

    def load_styles(self):
        return """
        QWidget {
            background-color: #0f111a;
            color: white;
            font-family: 'Segoe UI';
            font-size: 14px;
        }
        QLineEdit, QComboBox {
            background-color: #1a1d29;
            border: 1px solid #2c2f3a;
            border-radius: 8px;
            padding: 10px;
            color: white;
        }
        QPushButton {
            background-color: #1a1d29;
            border: none;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            color: white;
        }
        QPushButton:hover {
            background-color: #232737;
        }
        QPushButton#playButton {
            background-color: #3b5cff;
            font-size: 16px;
        }
        QPushButton#playButton:hover {
            background-color: #4d6aff;
        }
        QLabel#footer {
            color: #888;
            font-size: 11px;
        }
        """
    def move_logs_and_config(self):
        mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
        launcher_dir = get_appdata_path()

    # Move logs
        logs_src = os.path.join(mc_dir, "logs")
        logs_dst = os.path.join(launcher_dir, "logs")
        if os.path.exists(logs_src):
            shutil.rmtree(logs_dst, ignore_errors=True)
            shutil.copytree(logs_src, logs_dst)
            print("Copied logs to BarrieLauncher directory.")

    # Move config
        config_src = os.path.join(mc_dir, "config")
        config_dst = os.path.join(launcher_dir, "config")
        if os.path.exists(config_src):
            shutil.rmtree(config_dst, ignore_errors=True)
            shutil.copytree(config_src, config_dst)
            print("Copied config to BarrieLauncher directory.")

    # Move CustomSkinLoader
        skin_src = os.path.join(mc_dir, "CustomSkinLoader")
        skin_dst = os.path.join(launcher_dir, "CustomSkinLoader")
        if os.path.exists(skin_src):
            shutil.rmtree(skin_dst, ignore_errors=True)
            shutil.copytree(skin_src, skin_dst)
            print("Copied CustomSkinLoader to BarrieLauncher directory.")

    def on_play_clicked(self):
        username = self.username_input.text().strip()
        version_index = self.version_dropdown.currentIndex()
        version_id = self.version_dropdown.itemData(version_index)

# Save settings
        save_settings(username, version_id)

        self.auto_download_skin(username)
        if not username:
            QMessageBox.warning(self, "Missing Username", "Please enter a Minecraft username.")
            return

        version_index = self.version_dropdown.currentIndex()
        version_id = self.version_dropdown.itemData(version_index)
        edition = self.edition_dropdown.currentText()
        
        if not version_id:
            QMessageBox.warning(self, "Invalid Selection", "Please select a valid Minecraft version.")
            return

        settings = load_settings()
        allocated_ram_mb = settings.get("ram_mb", 2048)  # fallback 2 GB
        print(f"Allocated RAM from settings: {allocated_ram_mb} MB")
        


        options = {
            "username": username,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "token": "faketoken",
            "jvmArguments": [f"-Xmx{allocated_ram_mb}M", f"-Xms{allocated_ram_mb}M"]
        }
        

    # If Downloaded Versions checkbox is checked
        if self.downloaded_checkbox.isChecked():
            dialog = DownloadedVersionSelector(username, parent=self)
            dialog.exec_()
            return

        if self.downloaded_checkbox.isChecked():
            dialog = DownloadedVersionSelector(username, parent=self)
            dialog.exec_()
            return

        if edition.lower() == "fabric":
            # If downloaded_checkbox is *not* checked, install Fabric instead
            launch_minecraft(username, version_id, mode="Fabric")

        elif edition.lower() == "forge":
            self.install_and_launch_forge(username, version_id)

        else:
            try:
                minecraft_launcher_lib.install.install_minecraft_version(
                    version_id,
                    minecraft_launcher_lib.utils.get_minecraft_directory()
                )
                command = minecraft_launcher_lib.command.get_minecraft_command(
                version_id,
                minecraft_launcher_lib.utils.get_minecraft_directory(),
                options
                )

# Inject RAM allocation manually
                jvm_args = [f"-Xmx{allocated_ram_mb}M", f"-Xms{allocated_ram_mb}M"]
                command.insert(2, " ".join(jvm_args))  # Insert after 'java' and '-cp'
                print("Launching with command:", " ".join(command))


                self.hide()
                subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW).wait()
                self.show()
                self.move_logs_and_config()

            except Exception as e:
                QMessageBox.critical(self, "Launch Error", f"Failed to launch Minecraft:\n{e}")

        def install_customskinloader(self, fabric_version):
            mods_dir = os.path.join(minecraft_launcher_lib.utils.get_minecraft_directory(), "mods", fabric_version)
            os.makedirs(mods_dir, exist_ok=True)

            csl_path = os.path.join(mods_dir, "CustomSkinLoader.jar")
            if not os.path.exists(csl_path):
                try:
                    print("Downloading CustomSkinLoader...")
                    url = "https://github.com/xfl03/CustomSkinLoader/releases/latest/download/CustomSkinLoader_Fabric.jar"
                    r = requests.get(url, stream=True, timeout=15)
                    if r.status_code == 200:
                        with open(csl_path, "wb") as f:
                            shutil.copyfileobj(r.raw, f)
                        print("CustomSkinLoader installed.")
                    else:
                        print("Failed to download CustomSkinLoader.")
                except Exception as e:
                    print(f"Error downloading CustomSkinLoader: {e}")
    

    def open_mods_menu(self):
        mods_path = os.path.join(minecraft_launcher_lib.utils.get_minecraft_directory(), "mods")
        os.makedirs(mods_path, exist_ok=True)
        os.startfile(mods_path)  # Windows only




    def open_resourcepacks_folder(self):
        rp_path = os.path.join(minecraft_launcher_lib.utils.get_minecraft_directory(), "resourcepacks")
        os.makedirs(rp_path, exist_ok=True)
        os.startfile(rp_path)

    def open_sodium_installer(self):
        version_index = self.version_dropdown.currentIndex()
        version_id = self.version_dropdown.itemData(version_index)

        if not version_id:
            QMessageBox.warning(self, "No Version Selected", "Please select a Minecraft version first.")
            return

        mods_folder = os.path.join(minecraft_launcher_lib.utils.get_minecraft_directory(), "mods")
        os.makedirs(mods_folder, exist_ok=True)

        try:
            response = requests.get("https://api.modrinth.com/v2/project/AANobbMI/version", timeout=15)
            versions_data = response.json()
            for v in versions_data:
                if version_id in v["game_versions"]:
                    for file in v["files"]:
                        if file["filename"].endswith(".jar"):
                            sodium_url = file["url"]
                            sodium_file_path = os.path.join(mods_folder, file["filename"])
                            r = requests.get(sodium_url, stream=True, timeout=15)
                            if r.status_code == 200:
                                with open(sodium_file_path, "wb") as f:
                                    shutil.copyfileobj(r.raw, f)
                                QMessageBox.information(self, "Success", f"Sodium installed to mods folder:\n{file['filename']}")
                            else:
                                QMessageBox.warning(self, "Download Failed", "Failed to download the Sodium jar.")
                            return
            else:
                QMessageBox.warning(self, "Not Found", f"No Sodium version found for Minecraft {version_id}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error installing Sodium:\n{e}")

    def ensure_assets_exist(self):
        os.makedirs(self.assets_dir, exist_ok=True)
        os.makedirs(self.ads_dir, exist_ok=True)
        default_assets = {
            "logo.png": "https://i.postimg.cc/6px5gGRg/logo.png",
            "logo.ico": "https://raw.githubusercontent.com/firearz/Barrie-Launcher-Improved/refs/heads/main/icon.ico",
            "github.png": "https://img.icons8.com/?size=512&id=bVGqATNwfhYq&format=png",
            "youtube.png": "https://img.icons8.com/?size=512&id=szxM3fi4e37N&format=png",
            "instagram.png": "https://img.icons8.com/?size=512&id=YtpeVQhQ8USm&format=png"
        }
        for name, url in default_assets.items():
            path = os.path.join(self.assets_dir, name)
            if not os.path.exists(path):
                try:
                    r = requests.get(url, stream=True, timeout=10)
                    if r.status_code == 200:
                        with open(path, 'wb') as f:
                            shutil.copyfileobj(r.raw, f)
                except Exception as e:
                    print(f"Failed to download {name}: {e}")


if __name__ == "__main__":
    # Create AppData directory if it doesn't exist
    appdata_path = get_appdata_path()
    os.makedirs(appdata_path, exist_ok=True)

    # Change working directory to AppData/BarrieLauncher
    os.chdir(appdata_path)

    # Start the launcher UI
    app = QApplication(sys.argv)
    window = BarrieLauncher()
    window.show()
    sys.exit(app.exec())

