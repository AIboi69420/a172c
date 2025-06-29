import os
import sys
import platform
import shutil
import urllib.request
import zipfile
import subprocess

# ----------- Ensure ffmpeg is installed or downloaded -----------

# ----------- Virtual Environment and Package Setup -----------

REQUIREMENTS = [
    "llama-cpp-python",   # llama_cpp import comes from this package
    "pyqt6>=6.3.0",       # For HighDpiScaleFactorRoundingPolicy support
    "pillow",
    "edge-tts",
    "pyttsx3",
    "playsound==1.2.2",   # Updated to more stable version
    "pydub",
]

def run_command(cmd, shell=False):
    try:
        subprocess.run(cmd, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e.cmd}")
        print(f"💥 Error code: {e.returncode}")
        sys.exit(e.returncode)

def is_onedrive_path(path):
    return "onedrive" in path.lower()

def create_venv():
    venv_dir = "venv"
    if os.path.exists(venv_dir):
        print("ℹ️ Virtual environment already exists. Skipping creation.")
        return

    print("🔧 Creating virtual environment...")
    try:
        run_command([sys.executable, "-m", "venv", venv_dir])
        print("✅ Virtual environment created.\n")
    except PermissionError:
        print("❌ Permission denied while creating the virtual environment.")
        print("💡 Try running this script as Administrator or move the folder out of OneDrive.")
        sys.exit(1)

def install_requirements():
    print("📦 Installing packages in the virtual environment...")

    python_path = (
        os.path.join("venv", "Scripts", "python.exe") if platform.system() == "Windows"
        else os.path.join("venv", "bin", "python")
    )

    if not os.path.exists(python_path):
        print("❌ Python executable not found in virtual environment.")
        sys.exit(1)

    # Upgrade pip via python -m pip, not pip.exe directly
    run_command([python_path, "-m", "pip", "install", "--upgrade", "pip"])

    for pkg in REQUIREMENTS:
        run_command([python_path, "-m", "pip", "install", pkg])

    print("✅ All required packages installed.\n")

def run_chat_py():
    print("🚀 Launching chat.py...\n")

    python_path = (
        os.path.join("venv", "Scripts", "python.exe") if platform.system() == "Windows"
        else os.path.join("venv", "bin", "python")
    )

    if not os.path.exists("chat.py"):
        print("❌ chat.py not found in current directory.")
        sys.exit(1)

    run_command([python_path, "chat.py"])

# ----------- Main flow -----------

def main():
    # First ensure ffmpeg is installed or downloaded
    cwd = os.getcwd()
    if is_onedrive_path(cwd):
        print("⚠️ Warning: You're running this project inside a OneDrive folder.")
        print("🔁 This may cause file access errors. Consider moving it to a local folder like C:\\Projects.\n")

    create_venv()
    install_requirements()
    run_chat_py()

if __name__ == "__main__":
    main()
