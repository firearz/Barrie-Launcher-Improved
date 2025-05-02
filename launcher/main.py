import os
import sys
import webbrowser
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QStackedLayout, QFrame
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer
from launcher import get_available_versions, launch_minecraft  # Your custom logic

class BarrieLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Barrie Launcher")
        self.setFixedSize(900, 520)

        # --- Determine paths relative to this file ---
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.ads_dir = os.path.join(self.assets_dir, "ads")
        self.icon_path = os.path.join(self.assets_dir, "logo.png")

        self.setWindowIcon(QIcon(self.icon_path))
        self.setStyleSheet("background-color: #2c2c2c; color: white; font-family: 'Segoe UI';")

        main_layout = QHBoxLayout(self)

        # === Sidebar ===
        sidebar = QVBoxLayout()
        sidebar.setAlignment(Qt.AlignTop)

        # Logo
        logo = QLabel()
        logo_pixmap = QPixmap(self.icon_path)
        if not logo_pixmap.isNull():
            logo.setPixmap(logo_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        sidebar.addWidget(logo)

        # Sidebar Buttons
        links = [
            ("GitHub", "💻", "https://github.com"),
            ("YouTube", "▶️", "https://youtube.com"),
            ("Instagram", "📸", "https://instagram.com")
        ]
        for name, icon, url in links:
            btn = QPushButton(f"{icon} {name}")
            btn.setStyleSheet("background-color: #444; padding: 10px;")
            btn.clicked.connect(lambda _, link=url: webbrowser.open(link))
            sidebar.addWidget(btn)

        sidebar_frame = QFrame()
        sidebar_frame.setLayout(sidebar)
        sidebar_frame.setFixedWidth(160)
        sidebar_frame.setStyleSheet("background-color: #1a1a1a;")

        main_layout.addWidget(sidebar_frame)

        # === Main UI ===
        ui_layout = QVBoxLayout()

        # Username
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your Minecraft username")
        self.username_input.setFixedWidth(300)
        top_bar.addWidget(self.username_input)
        top_bar.addStretch()
        ui_layout.addLayout(top_bar)

        # Ad Banner
        self.ad_label = QLabel()
        self.ad_label.setFixedHeight(220)
        self.ad_label.setAlignment(Qt.AlignCenter)
        self.ad_label.setStyleSheet("background-color: #111; border: 1px solid #333;")
        ui_layout.addWidget(self.ad_label)

        # Load ad images
        self.ads = []
        self.ad_index = 0
        if os.path.exists(self.ads_dir):
            for file in sorted(os.listdir(self.ads_dir)):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    self.ads.append(os.path.join(self.ads_dir, file))

        self.update_ad()
        self.ad_timer = QTimer()
        self.ad_timer.timeout.connect(self.update_ad)
        self.ad_timer.start(3000)  # 3 seconds per ad

        # Bottom Bar (Version selector and Start)
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

        # Footer
        footer = QLabel("🔧 Made by @nextgenmilo | For Educational Purposes Only.")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 10px; color: gray; margin-top: 10px;")
        ui_layout.addWidget(footer)

        main_layout.addLayout(ui_layout)

    def update_ad(self):
        if not self.ads:
            self.ad_label.setText("No ads found in assets/ads/")
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

        self.hide()  # Hide launcher while game runs

        try:
            launch_minecraft(username, version_id)
        except Exception as e:
            print(f"Launch failed: {e}")
        finally:
            self.show()  # Reopen launcher after Minecraft closes


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = BarrieLauncher()
    launcher.show()
    sys.exit(app.exec())
