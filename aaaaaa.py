# Cleaned GUI version with speech-to-text only (TTS removed)

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import sqlite3
import threading
import json
import pyaudio
import vosk
import queue
import os

# --- VOICE SETUP (Speech-to-Text Only) ---
class VoiceHandler:
    def __init__(self):
        self.model = None
        self.sample_rate = 16000
        self.chunk_size = 4000
        self.audio_queue = queue.Queue()
        self.is_listening = False

        # Load Vosk model
        self.model_path = "vosk-model-en-us-0.22"
        if os.path.exists(self.model_path):
            try:
                self.model = vosk.Model(self.model_path)
                print("✅ Vosk model loaded successfully.")
            except Exception as e:
                print(f"❌ Failed to load Vosk model: {e}")
        else:
            print("⚠️ Vosk model not found. Please download and extract 'vosk-model-en-us-0.22'")
            print("🔗 https://alphacephei.com/vosk/models")

    def start_listening(self, callback):
        """Start continuous speech recognition using Vosk"""
        if not self.model:
            callback("Voice model not available. Please install Vosk model.")
            return

        def listen_thread():
            try:
                p = pyaudio.PyAudio()
                stream = p.open(format=pyaudio.paInt16,
                                channels=1,
                                rate=self.sample_rate,
                                input=True,
                                frames_per_buffer=self.chunk_size)
                recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
                self.is_listening = True

                while self.is_listening:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get('text', '').strip()
                        if text:
                            callback(text)

                stream.stop_stream()
                stream.close()
                p.terminate()

            except Exception as e:
                callback(f"Voice error: {str(e)}")

        threading.Thread(target=listen_thread, daemon=True).start()

    def stop_listening(self):
        """Stop speech recognition"""
        self.is_listening = False

# --- DB SETUP ---
conn = sqlite3.connect("fitness_data.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY,
    name TEXT, age INTEGER, gender TEXT, height REAL, weight REAL,
    goal TEXT, time_per_day INTEGER
)''')
conn.commit()

# --- API CALL TO OLLAMA ---
def query_llm(prompt):
    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "tinyllama",
            "prompt": prompt,
            "stream": False
        }, timeout=500)
        if response.status_code == 200:
            return response.json().get("response", "No response received")
        else:
            return f"API Error: Status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "⚠️ Cannot connect to Ollama. Please ensure Ollama is running on localhost:11434"
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. The AI model might be processing..."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# --- BASIC GUI (Stripped to voice input + chat only for brevity) ---
class FitnessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Fitness Coach - Voice Enabled")
        self.root.geometry("800x600")
        
        self.voice_handler = VoiceHandler()
        self.voice_enabled = False
        self.is_querying = False
        
        self.status_var = tk.StringVar(value="Ready")

        # UI Elements
        self.chat_history = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=20, font=("Consolas", 11))
        self.chat_history.pack(fill='both', expand=True, padx=10, pady=10)

        self.chat_entry = tk.Entry(root, font=('Arial', 12))
        self.chat_entry.pack(fill='x', padx=10, pady=(0, 5))
        self.chat_entry.bind('<Return>', lambda e: self.send_chat())

        button_frame = tk.Frame(root)
        button_frame.pack(fill='x', padx=10)

        self.send_button = ttk.Button(button_frame, text="Send", command=self.send_chat)
        self.send_button.pack(side='left')

        self.voice_button = ttk.Button(button_frame, text="🎤 Start Listening", command=self.toggle_listening)
        self.voice_button.pack(side='left', padx=5)

        self.status_label = tk.Label(root, textvariable=self.status_var, anchor='w')
        self.status_label.pack(fill='x', padx=10, pady=(5, 10))

        self.insert_welcome()

    def insert_welcome(self):
        msg = "👋 Welcome! Type or speak to your AI fitness coach.\n"
        self.chat_history.insert(tk.END, msg)
        self.chat_history.config(state='disabled')

    def toggle_listening(self):
        if not self.voice_enabled:
            self.voice_enabled = True
            self.status_var.set("🎤 Listening...")
            self.voice_button.config(text="🛑 Stop Listening")
            self.voice_handler.start_listening(self.handle_voice_input)
        else:
            self.voice_enabled = False
            self.status_var.set("🎤 Stopped")
            self.voice_button.config(text="🎤 Start Listening")
            self.voice_handler.stop_listening()

    def handle_voice_input(self, text):
        if "stop listening" in text.lower():
            self.root.after(0, self.toggle_listening)
            return
        self.root.after(0, lambda: self.process_voice_input(text))

    def process_voice_input(self, text):
        self.chat_entry.delete(0, tk.END)
        self.chat_entry.insert(0, text)
        self.send_chat(voice_input=True)

    def send_chat(self, voice_input=False):
        user_input = self.chat_entry.get().strip()
        if not user_input or self.is_querying:
            return

        self.chat_entry.delete(0, tk.END)
        self.chat_history.config(state='normal')
        prefix = "🎤 You (Voice)" if voice_input else "👤 You"
        self.chat_history.insert(tk.END, f"\n{prefix}: {user_input}\n")
        self.chat_history.config(state='disabled')
        self.chat_history.see(tk.END)

        self.is_querying = True
        self.status_var.set("🤖 Thinking...")
        self.send_button.config(state='disabled')
        threading.Thread(target=self.query_and_display, args=(user_input,), daemon=True).start()

    def query_and_display(self, prompt):
        response = query_llm(prompt)

        def update_ui():
            self.chat_history.config(state='normal')
            self.chat_history.insert(tk.END, f"🤖 AI Coach: {response}\n")
            self.chat_history.config(state='disabled')
            self.chat_history.see(tk.END)

            self.status_var.set("Ready")
            self.is_querying = False
            self.send_button.config(state='normal')

        self.root.after(0, update_ui)

# --- Start GUI ---
if __name__ == '__main__':
    root = tk.Tk()
    app = FitnessApp(root)
    root.mainloop()

