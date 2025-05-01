import os
import sys
import subprocess
import threading

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QFrame
)
from PySide6.QtGui import QPixmap, QIcon, QDesktopServices
from PySide6.QtCore import Qt, QTimer, QUrl

# Use relative paths from current script directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Import function from launcher.py
from launcher import get_available_versions  # Ensure this is a local file in the same directory


class BarrieLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Barrie Launcher")
        self.setWindowIcon(QIcon(os.path.join(BASE_DIR, "icon.png")))
        self.setFixedSize(900, 520)
        self.setStyleSheet("background-color: #2c2c2c; color: white; font-family: 'Segoe UI';")

        main_layout = QHBoxLayout(self)

        # === Sidebar ===
        sidebar = QVBoxLayout()
        sidebar.setAlignment(Qt.AlignTop)

        logo = QLabel()
        logo.setPixmap(QPixmap(os.path.join(BASE_DIR, "icon.png")).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        sidebar.addWidget(logo)

        for name, emoji, url in [
            ("GitHub", "💻", "https://github.com"),
            ("YouTube", "▶️", "https://youtube.com"),
            ("Instagram", "📸", "https://instagram.com")
        ]:
            btn = QPushButton(f"{emoji} {name}")
            btn.setStyleSheet("background-color: #444; padding: 10px; margin-top: 8px;")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, link=url: QDesktopServices.openUrl(QUrl(link)))
            sidebar.addWidget(btn)

        sidebar_frame = QFrame()
        sidebar_frame.setLayout(sidebar)
        sidebar_frame.setFixedWidth(160)
        sidebar_frame.setStyleSheet("background-color: #1a1a1a;")
        main_layout.addWidget(sidebar_frame)

        # === Main UI ===
        ui_layout = QVBoxLayout()

        # --- Username Input ---
        top_bar = QHBoxLayout()
        user_label = QLabel("Username :")
        user_label.setStyleSheet("font-size: 16px;")
        self.username_input = QLineEdit()
        self.username_input.setFixedWidth(300)
        self.username_input.setPlaceholderText("Enter your Minecraft username")
        top_bar.addWidget(user_label)
        top_bar.addWidget(self.username_input)
        top_bar.addStretch()
        ui_layout.addLayout(top_bar)

        # --- Advertisement Slideshow ---
        self.ad_label = QLabel()
        self.ad_label.setFixedHeight(220)
        self.ad_label.setAlignment(Qt.AlignCenter)
        self.ad_label.setStyleSheet("background-color: #000;")
        ui_layout.addWidget(self.ad_label)

        self.ads = []
        self.ad_index = 0
        ad_folder = os.path.join(BASE_DIR, "ads")
        if os.path.exists(ad_folder):
            for file in os.listdir(ad_folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.ads.append(os.path.join(ad_folder, file))

        self.update_ad()
        self.ad_timer = QTimer()
        self.ad_timer.timeout.connect(self.update_ad)
        self.ad_timer.start(3000)

        # --- Version Selector + Start Button ---
        bottom_row = QHBoxLayout()
        self.version_dropdown = QComboBox()
        self.version_map = {}
        for label, version_id in get_available_versions():
            self.version_dropdown.addItem(label)
            self.version_map[label] = version_id

        self.version_dropdown.setFixedWidth(160)
        start_btn = QPushButton("🚀 START")
        start_btn.setFixedWidth(160)
        start_btn.setStyleSheet("background-color: #6ab04c; font-size: 16px; padding: 10px; font-weight: bold;")
        start_btn.clicked.connect(self.launch_game)

        bottom_row.addWidget(self.version_dropdown)
        bottom_row.addWidget(start_btn)
        bottom_row.addStretch()
        ui_layout.addLayout(bottom_row)

        # --- Footer ---
        footer = QLabel("🔧 Made by @nextgenmilo | For Educational Use Only.")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 10px; color: gray; margin-top: 10px;")
        ui_layout.addWidget(footer)

        main_layout.addLayout(ui_layout)

    def update_ad(self):
        if not self.ads:
            self.ad_label.setText("No Images Found in /ads")
            return

        pixmap = QPixmap(self.ads[self.ad_index])
        self.ad_label.setPixmap(pixmap.scaled(self.ad_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.ad_index = (self.ad_index + 1) % len(self.ads)

    def launch_game(self):
        username = self.username_input.text().strip()
        selected_label = self.version_dropdown.currentText()
        version_id = self.version_map.get(selected_label)

        if not username:
            print("⚠️ Username is required.")
            return

        self.hide()

        def run_game():
            try:
                # Call launcher.py with args
                process = subprocess.Popen(
                    [sys.executable, os.path.join(BASE_DIR, "launcher.py"), username, version_id]
                )
                process.wait()
            except Exception as e:
                print(f"❌ Launch failed: {e}")
            self.show()

        threading.Thread(target=run_game, daemon=True).start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BarrieLauncher()
    window.show()
    sys.exit(app.exec())
