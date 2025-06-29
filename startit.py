import os
import sys
import platform
import urllib.request
import subprocess
from pathlib import Path
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# ----------- Virtual Environment and Package Setup -----------

REQUIREMENTS = [
    "llama-cpp-python",
    "pyqt6>=6.3.0",
    "pillow",
    "edge-tts",
    "pyttsx3",
    "playsound==1.2.2",
    "pydub",
]

MODEL_NAME = "openhermes-2-mistral-7b.Q4_K_M.gguf"
MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / MODEL_NAME
MODEL_URL = "https://huggingface.co/openhermes/openhermes-2-mistral-7b.Q4_K_M/resolve/main/openhermes-2-mistral-7b.Q4_K_M.gguf"

VENV_DIR = Path("venv")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Model Setup and Launcher")
        self.geometry("600x400")
        self.resizable(True, True)

        self.status_label = ttk.Label(self, text="Ready.", anchor="center")
        self.status_label.pack(pady=5, fill="x")

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=20, pady=5)

        self.log_text = scrolledtext.ScrolledText(self, height=15, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)

        self.start_button = ttk.Button(self, text="Start Setup and Launch", command=self.start_process)
        self.start_button.pack(pady=10)

    def log(self, message):
        # Append message to the log text widget, thread-safe using `after`
        def append():
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
        self.after(0, append)

    def set_status(self, text):
        def update():
            self.status_label.config(text=text)
        self.after(0, update)

    def start_process(self):
        self.start_button.config(state="disabled")
        threading.Thread(target=self.main_process, daemon=True).start()

    def main_process(self):
        try:
            cwd = Path.cwd()
            if "onedrive" in str(cwd).lower():
                self.log("⚠️ Warning: Running inside OneDrive folder.")
                self.set_status("⚠️ Warning: Running inside OneDrive folder.")

            self.progress.start()
            self.set_status("Downloading model...")
            self.log("Starting model download...")
            download_model(log_func=self.log)

            self.set_status("Creating virtual environment...")
            self.log("Creating virtual environment...")
            create_venv(log_func=self.log)

            self.set_status("Installing required packages...")
            self.log("Installing required packages...")
            install_requirements(log_func=self.log)

            self.progress.stop()
            self.set_status("Launching chat.py...")
            self.log("Launching chat.py...")
            run_chat_py(log_func=self.log)

            self.set_status("Done. chat.py is running.")
            self.log("chat.py launched successfully.")
        except Exception as e:
            self.progress.stop()
            self.set_status(f"Error: {e}")
            self.log(f"Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.start_button.config(state="normal")

def run_command(cmd, shell=False, log_func=print):
    log_func(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, shell=shell, check=True)

def create_venv(log_func=print):
    if VENV_DIR.exists():
        log_func("ℹ️ Virtual environment already exists. Skipping creation.")
        return

    log_func("🔧 Creating virtual environment...")
    run_command([sys.executable, "-m", "venv", str(VENV_DIR)], log_func=log_func)
    log_func("✅ Virtual environment created.\n")

def get_venv_python():
    if platform.system() == "Windows":
        python_exe = VENV_DIR / "Scripts" / "python.exe"
    else:
        python_exe = VENV_DIR / "bin" / "python"

    if not python_exe.exists():
        raise FileNotFoundError("Python executable not found in virtual environment.")
    return str(python_exe)

def install_requirements(log_func=print):
    python_path = get_venv_python()
    run_command([python_path, "-m", "pip", "install", "--upgrade", "pip"], log_func=log_func)
    for pkg in REQUIREMENTS:
        run_command([python_path, "-m", "pip", "install", pkg], log_func=log_func)
    log_func("✅ All required packages installed.\n")

def download_model(log_func=print):
    if not MODEL_DIR.exists():
        MODEL_DIR.mkdir(parents=True)
        log_func(f"📂 Created models directory at {MODEL_DIR}")

    if MODEL_PATH.exists():
        log_func(f"✅ Model already exists at {MODEL_PATH}. Skipping download.")
        return

    log_func(f"⬇️ Downloading model from {MODEL_URL} ...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    log_func(f"✅ Model downloaded successfully to {MODEL_PATH}\n")

def run_chat_py(log_func=print):
    python_path = get_venv_python()
    chat_path = Path("chat.py")
    if not chat_path.exists():
        raise FileNotFoundError("chat.py not found in current directory.")

    log_func("Starting chat.py in hidden mode...")
    if platform.system() == "Windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen(
            [python_path, str(chat_path)],
            startupinfo=startupinfo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True,
        )
    else:
        subprocess.Popen(
            [python_path, str(chat_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )
    log_func("chat.py launched successfully.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
