# 🏗️ Build Guide — Barrie Launcher

Welcome to the official build guide for **Barrie Launcher**, a Minecraft launcher built with **Python + PySide6**, supporting ad rotation, local asset extraction to `%APPDATA%`, and Minecraft version launching via `minecraft-launcher-lib`.

This guide is intended for developers and contributors who want to build, test, and package the launcher into a portable `.exe`.

---

## 📦 Requirements

| Dependency               | Version    | Notes                      |
|--------------------------|------------|----------------------------|
| Python                   | 3.10+      | Avoid 3.12+ for lib compatibility |
| [PyInstaller](https://pyinstaller.org)         | Latest     | For creating `.exe` builds |
| [PySide6](https://pypi.org/project/PySide6/)  | Latest     | UI framework (Qt for Python) |
| [minecraft-launcher-lib](https://pypi.org/project/minecraft-launcher-lib/) | Latest     | Minecraft launching logic |
| psutil                   | Latest     | Process cleanup            |

### ✅ Install All Requirements

```bash
pip install -r requirements.txt
