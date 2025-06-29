import os
import json
import shutil
import threading

from llama_cpp import Llama

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QTextEdit, QLineEdit, QFileDialog, QMessageBox, QComboBox, QDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout
)
from PyQt6.QtGui import QPixmap, QGuiApplication
from PyQt6.QtCore import Qt, pyqtSignal

AVATAR_DIR = "avatars"
MODEL_PATH = "models/openhermes-2-mistral-7b.Q4_K_M.gguf"
PERSONALITY_FILE = "personalities.json"

os.makedirs(AVATAR_DIR, exist_ok=True)
os.makedirs("models", exist_ok=True)

DARK_STYLE = """
QWidget{background:#121212;color:#e0e0e0;font-family:"Segoe UI"}
QPushButton{background:#2e2e2e;color:#f48fb1;border:1px solid #f48fb1;padding:6px 12px;border-radius:4px}
QPushButton:hover{background:#f48fb1;color:#121212}
QLineEdit,QTextEdit{background:#1e1e1e;color:#e0e0e0;border:1px solid #f48fb1;border-radius:4px}
QLabel{color:#e0e0e0}
QListWidget{background:#1e1e1e;color:#e0e0e0;border:1px solid #f48fb1;border-radius:4px}
QComboBox{background:#1e1e1e;color:#e0e0e0;border:1px solid #f48fb1;border-radius:4px;padding:2px 4px}
"""

def load_personalities():
    try:
        if os.path.exists(PERSONALITY_FILE):
            with open(PERSONALITY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        QMessageBox.warning(None, "Error", f"Could not load personalities: {e}")
    return {}

def save_personalities(d):
    try:
        with open(PERSONALITY_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=4)
    except Exception as e:
        QMessageBox.warning(None, "Error", f"Failed to save personalities: {e}")

class ChatSession:
    def __init__(self, model_path):
        self.model_path = model_path
        self.history = []
        try:
            self.llm = Llama(model_path=model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    def reset(self):
        self.history = []

    def add_message(self, role, text):
        self.history.append((role, text))

    def _build_prompt(self, new_input):
        system_msgs = [msg for role, msg in self.history if role == "system"]
        user_msgs = [(role, text) for role, text in self.history if role != "system"]
        MAX_EXCHANGES = 10
        trimmed_history = user_msgs[-MAX_EXCHANGES:]
        prompt_parts = [f"{'User:' if r == 'user' else 'Assistant:'} {t}" for r, t in trimmed_history]
        prompt_text = "\n".join(prompt_parts)
        return (system_msgs[0] + "\n" if system_msgs else "") + prompt_text + f"\nUser: {new_input}\nAssistant: "

    def generate_response(self, prompt, max_tokens=512):
        full_prompt = self._build_prompt(prompt)
        result = self.llm(full_prompt, max_tokens=max_tokens, stop=["User:", "Assistant:"])
        text = result.get("choices", [{}])[0].get("text", "").strip()
        self.add_message("assistant", text)
        return text

class PersonalityEditor(QDialog):
    FIELDS = [
        ("Name", "name"),
        ("Age", "age"),
        ("Race / Species", "race"),
        ("Role", "role"),
        ("Gender", "gender"),
        ("Backstory", "backstory"),
        ("Default Mood", "mood"),
        ("Interests (comma-separated)", "interests"),
        ("Dialogue Style", "dialogue_style"),
        ("Other Traits / Quirks (comma-separated)", "tags")
    ]

    def __init__(self, parent=None, personality=None):
        super().__init__(parent)
        self.setWindowTitle("Personality Editor")
        self.setMinimumWidth(400)
        self.personality = personality or {}

        self.layout = QVBoxLayout()
        self.grid = QGridLayout()

        self.inputs = {}

        for i, (label, key) in enumerate(self.FIELDS):
            lbl = QLabel(label)
            inp = QTextEdit() if key in ("backstory", "dialogue_style") else QLineEdit()
            if isinstance(inp, QTextEdit):
                inp.setFixedHeight(80)
            self.grid.addWidget(lbl, i, 0)
            self.grid.addWidget(inp, i, 1)
            self.inputs[key] = inp

        self.layout.addLayout(self.grid)

        self.avatar_path = self.personality.get("avatar", "")
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(150, 150)
        self.avatar_label.setStyleSheet("border: 1px solid #f48fb1;")
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_avatar(self.avatar_path)
        self.layout.addWidget(QLabel("Avatar:"))
        self.layout.addWidget(self.avatar_label)

        self.btn_avatar = QPushButton("Choose Avatar")
        self.btn_avatar.clicked.connect(self.choose_avatar)
        self.layout.addWidget(self.btn_avatar)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        self.layout.addLayout(btn_layout)

        self.setLayout(self.layout)
        if personality:
            self.load_personality()

    def load_personality(self):
        for key, inp in self.inputs.items():
            val = self.personality.get(key, "")
            inp.setPlainText(val) if isinstance(inp, QTextEdit) else inp.setText(val)

    def choose_avatar(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select Avatar Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if fname:
            base = os.path.basename(fname)
            dest = os.path.join(AVATAR_DIR, base)
            try:
                shutil.copy(fname, dest)
                self.avatar_path = dest
                self.set_avatar(dest)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to copy avatar: {e}")

    def set_avatar(self, path):
        if path and os.path.exists(path):
            try:
                self.avatar_label.setPixmap(QPixmap(path).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
            except:
                self.avatar_label.setText("Avatar Load Error")
        else:
            self.avatar_label.setText("No Avatar")

    def get_personality_data(self):
        data = {}
        for key, inp in self.inputs.items():
            val = inp.toPlainText().strip() if isinstance(inp, QTextEdit) else inp.text().strip()
            data[key] = [x.strip() for x in val.split(",") if x.strip()] if key in ["interests", "tags"] else val
        data["avatar"] = self.avatar_path
        return data

class ChatApp(QWidget):
    response_ready = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Llama Chat App")
        self.resize(1000, 700)
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

        self.personalities = load_personalities()
        self.current_persona_key = None
        self.chat_session = None

        self.init_ui()
        self.response_ready.connect(self.on_response_ready)

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        left = QVBoxLayout()
        self.personality_list = QListWidget()
        self.personality_list.itemClicked.connect(self.personality_selected)
        left.addWidget(QLabel("Personalities"))
        left.addWidget(self.personality_list)

        btns = QHBoxLayout()
        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self.add_personality)
        btn_delete = QPushButton("Delete")
        btn_delete.clicked.connect(self.delete_personality)
        btns.addWidget(btn_add)
        btns.addWidget(btn_delete)
        left.addLayout(btns)

        self.avatar_label = QLabel("No Avatar")
        self.avatar_label.setFixedSize(200, 200)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setStyleSheet("border: 1px solid #f48fb1;")
        left.addWidget(self.avatar_label)

        main_layout.addLayout(left, 1)

        right = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        right.addWidget(self.chat_display, 5)

        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_line)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        right.addLayout(input_layout)

        self.start_btn = QPushButton("Start Chat")
        self.start_btn.clicked.connect(self.start_chat)
        right.addWidget(self.start_btn)

        main_layout.addLayout(right, 3)
        self.setStyleSheet(DARK_STYLE)
        self.reload_personality_list()
        self.set_chat_enabled(False)

    def reload_personality_list(self):
        self.personality_list.clear()
        for key in sorted(self.personalities):
            self.personality_list.addItem(QListWidgetItem(key))

    def personality_selected(self, item):
        key = item.text()
        self.current_persona_key = key
        p = self.personalities[key]
        self.avatar_label.setPixmap(QPixmap(p["avatar"]).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)) if p.get("avatar") and os.path.exists(p["avatar"]) else self.avatar_label.setText("No Avatar")

    def add_personality(self):
        dlg = PersonalityEditor(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_personality_data()
            if not data.get("name"):
                QMessageBox.warning(self, "Invalid", "Name required.")
                return
            if data["name"] in self.personalities:
                QMessageBox.warning(self, "Duplicate", "A personality with this name already exists.")
                return
            self.personalities[data["name"]] = data
            save_personalities(self.personalities)
            self.reload_personality_list()

    def delete_personality(self):
        item = self.personality_list.currentItem()
        if item:
            key = item.text()
            reply = QMessageBox.question(self, "Confirm Delete", f"Delete personality '{key}'?")
            if reply == QMessageBox.StandardButton.Yes:
                self.personalities.pop(key, None)
                save_personalities(self.personalities)
                self.reload_personality_list()
                self.avatar_label.setText("No Avatar")
                if self.current_persona_key == key:
                    self.current_persona_key = None
                    self.set_chat_enabled(False)

    def start_chat(self):
        if not self.current_persona_key:
            QMessageBox.warning(self, "Select Personality", "Please select a personality to start chatting.")
            return
        try:
            self.chat_session = ChatSession(MODEL_PATH)
        except Exception as e:
            QMessageBox.critical(self, "Model Load Error", str(e))
            return

        self.chat_display.clear()
        self.set_chat_enabled(True)
        p = self.personalities[self.current_persona_key]
        system_prompt = (
            f"You are {p.get('name', 'Unknown')}\nAge: {p.get('age', 'Unknown')}\n"
            f"Race/Species: {p.get('race', 'Unknown')}\nRole: {p.get('role', 'Unknown')}\n"
            f"Gender: {p.get('gender', 'Unknown')}\nBackstory: {p.get('backstory', '')}\n"
            f"Default Mood: {p.get('mood', '')}\nInterests: {', '.join(p.get('interests', []))}\n"
            f"Dialogue Style: {p.get('dialogue_style', '')}\nOther Traits: {', '.join(p.get('tags', []))}\n"
            "Answer as this character would."
        )
        self.chat_session.add_message("system", system_prompt)
        self.append_chat("System", "Chat started. Say hi!")

    def set_chat_enabled(self, enabled):
        self.input_line.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)

    def append_chat(self, sender, text):
        self.chat_display.append(f"<b>{sender}:</b> {text}")

    def send_message(self):
        if not self.chat_session:
            return
        user_text = self.input_line.text().strip()
        if not user_text:
            return

        self.append_chat("You", user_text)
        self.chat_session.add_message("user", user_text)
        self.input_line.clear()
        self.send_btn.setEnabled(False)
        self.input_line.setEnabled(False)

        def worker():
            try:
                response = self.chat_session.generate_response(user_text)
                self.response_ready.emit(response)
            except Exception as e:
                self.response_ready.emit(f"[Error] {e}")

        threading.Thread(target=worker, daemon=True).start()

    def on_response_ready(self, response_text):
        self.append_chat(self.current_persona_key or "Assistant", response_text)
        self.send_btn.setEnabled(True)
        self.input_line.setEnabled(True)

if __name__ == "__main__":
    app = QApplication([])
    win = ChatApp()
    win.show()
    app.exec()
