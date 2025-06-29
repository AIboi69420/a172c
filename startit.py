import os
import sys
import platform
import urllib.request
import subprocess
import shutil
from pathlib import Path

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

MODEL_NAME = "openhermes-2-mistral-7b.Q4_K_M.gguf"
MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / MODEL_NAME
MODEL_URL = "https://huggingface.co/openhermes/openhermes-2-mistral-7b.Q4_K_M/resolve/main/openhermes-2-mistral-7b.Q4_K_M.gguf"
# Replace with the actual direct URL of your model file

VENV_DIR = Path("venv")

def run_command(cmd, shell=False):
    try:
        subprocess.run(cmd, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e.cmd}")
        print(f"💥 Error code: {e.returncode}")
        sys.exit(e.returncode)

def is_onedrive_path(path):
    # Lowercase and check if 'onedrive' exists in any part of the path
    path_str = str(path).lower()
    return "onedrive" in path_str

def create_venv():
    if VENV_DIR.exists():
        print("ℹ️ Virtual environment already exists. Skipping creation.")
        return

    print("🔧 Creating virtual environment...")
    try:
        run_command([sys.executable, "-m", "venv", str(VENV_DIR)])
        print("✅ Virtual environment created.\n")
    except PermissionError:
        print("❌ Permission denied while creating the virtual environment.")
        print("💡 Try running this script as Administrator/root or move the folder out of OneDrive.")
        sys.exit(1)

def get_venv_python():
    # Use platform-agnostic way to find python in venv
    if platform.system() == "Windows":
        python_exe = VENV_DIR / "Scripts" / "python.exe"
    else:
        python_exe = VENV_DIR / "bin" / "python"

    if not python_exe.exists():
        print("❌ Python executable not found in virtual environment.")
        sys.exit(1)
    return str(python_exe)

def install_requirements():
    print("📦 Installing packages in the virtual environment...")

    python_path = get_venv_python()

    # Upgrade pip first
    run_command([python_path, "-m", "pip", "install", "--upgrade", "pip"])

    for pkg in REQUIREMENTS:
        run_command([python_path, "-m", "pip", "install", pkg])

    print("✅ All required packages installed.\n")

def download_model():
    if not MODEL_DIR.exists():
        MODEL_DIR.mkdir(parents=True)
        print(f"📂 Created models directory at {MODEL_DIR}")

    if MODEL_PATH.exists():
        print(f"✅ Model already exists at {MODEL_PATH}. Skipping download.")
        return

    print(f"⬇️ Downloading model from {MODEL_URL} ...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print(f"✅ Model downloaded successfully to {MODEL_PATH}\n")
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        sys.exit(1)

def run_chat_py():
    print("🚀 Launching chat.py...\n")

    python_path = get_venv_python()

    chat_path = Path("chat.py")
    if not chat_path.exists():
        print("❌ chat.py not found in current directory.")
        sys.exit(1)

    run_command([python_path, str(chat_path)])

# ----------- Main flow -----------

def main():
    cwd = Path.cwd()
    if is_onedrive_path(cwd):
        print("⚠️ Warning: You're running this project inside a OneDrive folder.")
        print("🔁 This may cause file access errors. Consider moving it to a local folder.\n")

    download_model()
    create_venv()
    install_requirements()
    run_chat_py()

if __name__ == "__main__":
    main()
