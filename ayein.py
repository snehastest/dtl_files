import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import sqlite3
import threading
import json
import queue
import os

# Voice imports (optional - will gracefully handle if not available)
try:
    import pyaudio
    import vosk
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("⚠️ Voice libraries not available. Install pyaudio and vosk for voice functionality.")

# --- VOICE SETUP (Speech-to-Text Only) ---
class VoiceHandler:
    def __init__(self):
        self.model = None
        self.sample_rate = 16000
        self.chunk_size = 4000
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.voice_available = VOICE_AVAILABLE

        if not self.voice_available:
            return

        # Load Vosk model
        self.model_path = "vosk-model-en-us-0.22"
        if os.path.exists(self.model_path):
            try:
                self.model = vosk.Model(self.model_path)
                print("✅ Vosk model loaded successfully.")
            except Exception as e:
                print(f"❌ Failed to load Vosk model: {e}")
                self.voice_available = False
        else:
            print("⚠️ Vosk model not found. Please download and extract 'vosk-model-en-us-0.22'")
            print("🔗 https://alphacephei.com/vosk/models")
            self.voice_available = False

    def start_listening(self, callback):
        """Start continuous speech recognition using Vosk"""
        if not self.voice_available or not self.model:
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

# --- VIBRANT PROFESSIONAL GUI APP WITH VOICE ---
class FitnessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🏋️ AI Fitness Coach Pro - Voice Enabled")
        self.root.geometry("1000x750")
        self.root.minsize(900, 650)
        
        # Set vibrant gradient background
        self.root.configure(bg='#667eea')
        
        # Initialize voice handler
        self.voice_handler = VoiceHandler()
        self.voice_enabled = False
        
        # Configure vibrant professional styling
        self.setup_colorful_styles()
        
        # Main container with gradient background
        main_frame = tk.Frame(root, bg='#667eea', padx=15, pady=15)
        main_frame.pack(fill='both', expand=True)
        
        # Header with gradient
        self.create_vibrant_header(main_frame)
        
        # Notebook with colorful styling
        self.notebook = ttk.Notebook(main_frame, style="Colorful.TNotebook")
        self.notebook.pack(fill='both', expand=True, pady=(25, 0))
        
        self.is_querying = False
        self.create_colorful_chat_tab()
        self.create_colorful_profile_tab()
        self.create_colorful_workout_tab()
        self.create_colorful_nutrition_tab()
        
        # Colorful status bar
        self.create_colorful_status_bar(main_frame)

    def setup_colorful_styles(self):
        """Configure vibrant professional styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colorful notebook style
        style.configure("Colorful.TNotebook", 
                       background='#667eea',
                       borderwidth=0,
                       tabmargins=[5, 5, 5, 0])
        
        style.configure("Colorful.TNotebook.Tab", 
                       padding=[25, 15],
                       font=('Arial', 11, 'bold'),
                       background='#764ba2',
                       foreground='white',
                       focuscolor='none')
        
        style.map("Colorful.TNotebook.Tab",
                 background=[('selected', '#f093fb'),
                            ('active', '#f093fb')])
        
        # Vibrant button styles
        style.configure("Primary.TButton", 
                       font=('Arial', 12, 'bold'),
                       background='#ff6b6b',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(25, 12))
        
        style.map("Primary.TButton",
                 background=[('active', '#ff5252'),
                            ('pressed', '#ff1744')])
        
        style.configure("Voice.TButton", 
                       font=('Arial', 11, 'bold'),
                       background='#9c27b0',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 10))
        
        style.map("Voice.TButton",
                 background=[('active', '#8e24aa'),
                            ('pressed', '#7b1fa2')])
        
        style.configure("Success.TButton", 
                       font=('Arial', 11, 'bold'),
                       background='#4ecdc4',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        
        style.map("Success.TButton",
                 background=[('active', '#26d0ce'),
                            ('pressed', '#00bcd4')])
        
        style.configure("Warning.TButton", 
                       font=('Arial', 11, 'bold'),
                       background='#ffa726',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        
        style.map("Warning.TButton",
                 background=[('active', '#ff9800'),
                            ('pressed', '#f57c00')])
        
        # Colorful label styles
        style.configure("Header.TLabel", 
                       font=('Arial', 28, 'bold'),
                       background='#667eea',
                       foreground='white')
        
        style.configure("Subtitle.TLabel", 
                       font=('Arial', 14),
                       background='#667eea',
                       foreground='#e8eaf6')
        
        style.configure("Section.TLabel", 
                       font=('Arial', 16, 'bold'),
                       background='white',
                       foreground='#2c3e50')
        
        style.configure("Field.TLabel", 
                       font=('Arial', 11, 'bold'),
                       background='white',
                       foreground='#34495e')
        
        # Colorful frame styles
        style.configure("Card.TFrame",
                       background='white',
                       relief='flat',
                       borderwidth=1)
        
        style.configure("Gradient.TFrame",
                       background='#667eea')
        
        # Entry and combobox styles
        style.configure("Colorful.TEntry",
                       font=('Arial', 11),
                       borderwidth=2,
                       focuscolor='#667eea')
        
        style.configure("Colorful.TCombobox",
                       font=('Arial', 11),
                       borderwidth=2,
                       focuscolor='#667eea')

    def create_vibrant_header(self, parent):
        """Create vibrant gradient header"""
        header_frame = tk.Frame(parent, bg='#667eea', height=120)
        header_frame.pack(fill='x', pady=(0, 15))
        header_frame.pack_propagate(False)
        
        ttk.Label(header_frame, text="🏋️ AI FITNESS COACH PRO", 
                 style="Header.TLabel").pack(pady=(20, 5))
        subtitle_text = "Transform Your Body with AI-Powered Fitness Intelligence"
        if self.voice_handler.voice_available:
            subtitle_text += " • Voice Enabled 🎤"
        ttk.Label(header_frame, text=subtitle_text, 
                 style="Subtitle.TLabel").pack()
        
        # Gradient separator
        separator_frame = tk.Frame(header_frame, bg='#f093fb', height=4)
        separator_frame.pack(fill='x', pady=(15, 0))

    def create_colorful_status_bar(self, parent):
        """Create colorful status bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("🚀 Ready to transform your fitness journey!")
        
        status_frame = tk.Frame(parent, bg='#667eea')
        status_frame.pack(fill='x', side='bottom', pady=(15, 0))
        
        # Colorful separator
        separator = tk.Frame(status_frame, bg='#f093fb', height=3)
        separator.pack(fill='x', pady=(0, 8))
        
        status_label = tk.Label(status_frame, 
                               textvariable=self.status_var,
                               font=('Arial', 10, 'bold'),
                               bg='#667eea',
                               fg='white')
        status_label.pack(anchor='w')

    def create_colorful_chat_tab(self):
        """Create vibrant chat interface with voice integration"""
        # Main container with white background
        container = tk.Frame(self.notebook, bg='white')
        self.notebook.add(container, text='💬 AI Chat Assistant')
        
        self.chat_tab = tk.Frame(container, bg='white', padx=20, pady=20)
        self.chat_tab.pack(fill='both', expand=True)

        # Colorful header
        header_frame = tk.Frame(self.chat_tab, bg='#667eea', height=60)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🤖 Chat with Your AI Fitness Coach", 
                font=('Arial', 16, 'bold'), bg='#667eea', fg='white').pack(pady=15)

        # Chat history with colorful styling
        chat_container = tk.Frame(self.chat_tab, bg='#f8f9fa', relief='solid', bd=2)
        chat_container.pack(fill='both', expand=True, pady=(0, 20))
        
        self.chat_history = scrolledtext.ScrolledText(
            chat_container, 
            height=16, 
            wrap=tk.WORD,
            font=('Consolas', 11),
            bg='#f8f9fa',
            fg='#2c3e50',
            relief='flat',
            borderwidth=0,
            padx=15,
            pady=15
        )
        self.chat_history.pack(fill='both', expand=True, padx=3, pady=3)
        
        # Colorful welcome message
        welcome_msg = """🎉 Welcome to AI Fitness Coach Pro! 🎉

🤖 AI Coach: Hello there, fitness enthusiast! I'm your personal AI fitness coach, powered by advanced AI technology. I'm here to help you achieve your fitness goals!

💪 Ask me about:
* Custom workout routines
* Nutrition and meal planning  
* Exercise form and techniques
* Motivation and goal setting
* Recovery and rest strategies

"""
        if self.voice_handler.voice_available:
            welcome_msg += "🎤 Voice Recognition: You can type OR speak your questions!\n* Click 'Start Listening' to use voice input\n* Say 'stop listening' to end voice mode\n\n"
        else:
            welcome_msg += "💬 Type your questions below to get started!\n\n"
        
        welcome_msg += "Let's start your transformation journey! What would you like to know? 🚀\n\n"
        
        self.chat_history.insert(tk.END, welcome_msg)
        self.chat_history.config(state='disabled')

        # Colorful input section with voice controls
        input_frame = tk.Frame(self.chat_tab, bg='#667eea', padx=20, pady=15)
        input_frame.pack(fill='x')
        
        tk.Label(input_frame, text="💬 Your Message:", 
                font=('Arial', 12, 'bold'), bg='#667eea', fg='white').pack(anchor='w')
        
        entry_container = tk.Frame(input_frame, bg='#667eea')
        entry_container.pack(fill='x', pady=(8, 0))
        
        self.chat_entry = tk.Entry(entry_container, 
                                  font=('Arial', 12),
                                  bg='white',
                                  fg='#2c3e50',
                                  relief='flat',
                                  bd=5)
        self.chat_entry.pack(side='left', fill='x', expand=True, padx=(0, 15), ipady=8)
        self.chat_entry.bind('<Return>', lambda e: self.send_chat())
        
        # Button container for send and voice buttons
        button_container = tk.Frame(entry_container, bg='#667eea')
        button_container.pack(side='right')
        
        self.send_button = ttk.Button(button_container, text="🚀 Send", 
                                     command=self.send_chat, style="Primary.TButton")
        self.send_button.pack(side='left', padx=(0, 10))
        
        # Voice button (only show if voice is available)
        if self.voice_handler.voice_available:
            self.voice_button = ttk.Button(button_container, text="🎤 Start Listening", 
                                          command=self.toggle_listening, style="Voice.TButton")
            self.voice_button.pack(side='left')

    def toggle_listening(self):
        """Toggle voice listening mode"""
        if not self.voice_handler.voice_available:
            messagebox.showwarning("Voice Not Available", 
                                 "Voice recognition is not available. Please install pyaudio and vosk packages, and download the Vosk model.")
            return
            
        if not self.voice_enabled:
            self.voice_enabled = True
            self.status_var.set("🎤 Listening for your voice... Speak now!")
            self.voice_button.config(text="🛑 Stop Listening")
            self.voice_handler.start_listening(self.handle_voice_input)
        else:
            self.voice_enabled = False
            self.status_var.set("🎤 Voice listening stopped")
            self.voice_button.config(text="🎤 Start Listening")
            self.voice_handler.stop_listening()

    def handle_voice_input(self, text):
        """Handle voice input from speech recognition"""
        if "stop listening" in text.lower():
            self.root.after(0, self.toggle_listening)
            return
        self.root.after(0, lambda: self.process_voice_input(text))

    def process_voice_input(self, text):
        """Process voice input and send as chat message"""
        self.chat_entry.delete(0, tk.END)
        self.chat_entry.insert(0, text)
        self.send_chat(voice_input=True)

    def send_chat(self, voice_input=False):
        """Send chat message with voice indicator"""
        user_input = self.chat_entry.get().strip()
        if not user_input or self.is_querying:
            return

        self.chat_history.config(state='normal')
        prefix = "🎤 You (Voice)" if voice_input else "👤 You"
        self.chat_history.insert(tk.END, f"\n{prefix}: {user_input}\n")
        self.chat_history.config(state='disabled')
        self.chat_history.see(tk.END)
        
        self.chat_entry.delete(0, tk.END)
        self.is_querying = True
        self.send_button.config(state='disabled', text="🔄 Processing...")
        self.status_var.set("🤖 AI is thinking... Please wait!")

        threading.Thread(target=self.query_and_display, args=(user_input,), daemon=True).start()

    def create_colorful_profile_tab(self):
        """Create vibrant profile management"""
        container = tk.Frame(self.notebook, bg='white')
        self.notebook.add(container, text='👤 Profile & Goals')
        
        self.profile_tab = tk.Frame(container, bg='white', padx=20, pady=20)
        self.profile_tab.pack(fill='both', expand=True)

        # Vibrant header
        header_frame = tk.Frame(self.profile_tab, bg='#4ecdc4', height=70)
        header_frame.pack(fill='x', pady=(0, 25))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="👤 Personal Profile & Fitness Goals", 
                font=('Arial', 18, 'bold'), bg='#4ecdc4', fg='white').pack(pady=(20, 5))
        tk.Label(header_frame, text="Tell us about yourself to get personalized recommendations", 
                font=('Arial', 11), bg='#4ecdc4', fg='white').pack()

        # Main container with colorful cards
        main_container = tk.Frame(self.profile_tab, bg='white')
        main_container.pack(fill='both', expand=True)
        
        # Left card - Personal Info
        left_card = tk.Frame(main_container, bg='#e3f2fd', relief='solid', bd=2)
        left_card.pack(side='left', fill='both', expand=True, padx=(0, 15))
        
        left_header = tk.Frame(left_card, bg='#2196f3', height=50)
        left_header.pack(fill='x')
        left_header.pack_propagate(False)
        tk.Label(left_header, text="📝 Personal Information", 
                font=('Arial', 14, 'bold'), bg='#2196f3', fg='white').pack(pady=12)
        
        left_content = tk.Frame(left_card, bg='#e3f2fd', padx=20, pady=20)
        left_content.pack(fill='both', expand=True)
        
        # Right card - Goals
        right_card = tk.Frame(main_container, bg='#e8f5e8', relief='solid', bd=2)
        right_card.pack(side='right', fill='both', expand=True, padx=(15, 0))
        
        right_header = tk.Frame(right_card, bg='#4caf50', height=50)
        right_header.pack(fill='x')
        right_header.pack_propagate(False)
        tk.Label(right_header, text="🎯 Fitness Goals", 
                font=('Arial', 14, 'bold'), bg='#4caf50', fg='white').pack(pady=12)
        
        right_content = tk.Frame(right_card, bg='#e8f5e8', padx=20, pady=20)
        right_content.pack(fill='both', expand=True)

        self.entries = {}
        
        # Personal info fields with colorful styling
        personal_fields = [
            ('Name', 'text', '👤'),
            ('Age', 'number', '🎂'),
            ('Gender', 'combo', '⚧'),
            ('Height (cm)', 'number', '📏'),
            ('Weight (kg)', 'number', '⚖️')
        ]
        
        for i, (label, field_type, icon) in enumerate(personal_fields):
            field_frame = tk.Frame(left_content, bg='#e3f2fd')
            field_frame.pack(fill='x', pady=8)
            
            tk.Label(field_frame, text=f"{icon} {label}", 
                    font=('Arial', 11, 'bold'), bg='#e3f2fd', fg='#1976d2').pack(anchor='w', pady=(0, 5))
            
            if field_type == 'combo' and label == 'Gender':
                self.entries[label] = ttk.Combobox(field_frame, 
                                                  values=['Male', 'Female', 'Other'], 
                                                  state='readonly', 
                                                  font=('Arial', 11),
                                                  style="Colorful.TCombobox")
            else:
                self.entries[label] = tk.Entry(field_frame, 
                                              font=('Arial', 11),
                                              bg='white',
                                              fg='#2c3e50',
                                              relief='solid',
                                              bd=2)
            
            self.entries[label].pack(fill='x', ipady=5)

        # Goals fields with colorful styling
        goal_fields = [
            ('Goal', 'combo', '🎯'),
            ('Time/Day (min)', 'number', '⏰')
        ]
        
        goals = ['Weight Loss', 'Muscle Gain', 'General Fitness', 'Endurance', 'Strength Training']
        
        for i, (label, field_type, icon) in enumerate(goal_fields):
            field_frame = tk.Frame(right_content, bg='#e8f5e8')
            field_frame.pack(fill='x', pady=8)
            
            tk.Label(field_frame, text=f"{icon} {label}", 
                    font=('Arial', 11, 'bold'), bg='#e8f5e8', fg='#2e7d32').pack(anchor='w', pady=(0, 5))
            
            if field_type == 'combo':
                self.entries[label] = ttk.Combobox(field_frame, 
                                                  values=goals, 
                                                  state='readonly', 
                                                  font=('Arial', 11),
                                                  style="Colorful.TCombobox")
            else:
                self.entries[label] = tk.Entry(field_frame, 
                                              font=('Arial', 11),
                                              bg='white',
                                              fg='#2c3e50',
                                              relief='solid',
                                              bd=2)
            
            self.entries[label].pack(fill='x', ipady=5)

        self.load_profile()

        # Colorful buttons
        button_frame = tk.Frame(self.profile_tab, bg='white')
        button_frame.pack(fill='x', pady=(25, 0))
        
        ttk.Button(button_frame, text="💾 Save Profile", command=self.save_profile, 
                  style="Success.TButton").pack(side='left', padx=(0, 15))
        ttk.Button(button_frame, text="🔄 Reload Profile", command=self.load_profile, 
                  style="Warning.TButton").pack(side='left')

    def load_profile(self):
        """Load existing profile data"""
        try:
            c.execute("SELECT * FROM user_profile LIMIT 1")
            profile = c.fetchone()
            if profile:
                fields = ['Name', 'Age', 'Gender', 'Height (cm)', 'Weight (kg)', 'Goal', 'Time/Day (min)']
                for i, field in enumerate(fields):
                    if profile[i+1] is not None:
                        if isinstance(self.entries[field], ttk.Combobox):
                            self.entries[field].set(str(profile[i+1]))
                        else:
                            self.entries[field].delete(0, tk.END)
                            self.entries[field].insert(0, str(profile[i+1]))
        except Exception as e:
            print(f"Error loading profile: {e}")

    def save_profile(self):
        """Save profile with validation"""
        try:
            required_fields = ['Name', 'Age', 'Height (cm)', 'Weight (kg)']
            for field in required_fields:
                if not self.entries[field].get().strip():
                    messagebox.showerror("Validation Error", f"Please fill in the {field} field.")
                    return
            
            data = [self.entries[label].get() for label in 
                   ['Name', 'Age', 'Gender', 'Height (cm)', 'Weight (kg)', 'Goal', 'Time/Day (min)']]
            
            c.execute("DELETE FROM user_profile")
            c.execute("INSERT INTO user_profile (name, age, gender, height, weight, goal, time_per_day) VALUES (?, ?, ?, ?, ?, ?, ?)", data)
            conn.commit()
            
            messagebox.showinfo("Success", "✅ Profile saved successfully!")
            self.status_var.set("🎉 Profile updated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save profile: {e}")

    def create_colorful_workout_tab(self):
        """Create vibrant workout planning interface"""
        container = tk.Frame(self.notebook, bg='white')
        self.notebook.add(container, text='🏋️ Workout Plans')
        
        self.workout_tab = tk.Frame(container, bg='white', padx=20, pady=20)
        self.workout_tab.pack(fill='both', expand=True)

        # Vibrant header
        header_frame = tk.Frame(self.workout_tab, bg='#ff6b6b', height=80)
        header_frame.pack(fill='x', pady=(0, 25))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🏋️ AI-Powered Workout Plans", 
                font=('Arial', 18, 'bold'), bg='#ff6b6b', fg='white').pack(pady=(15, 5))
        tk.Label(header_frame, text="Get personalized workout routines designed just for you", 
                font=('Arial', 11), bg='#ff6b6b', fg='white').pack()

        # Workout display with colorful container
        display_container = tk.Frame(self.workout_tab, bg='#fff3e0', relief='solid', bd=2)
        display_container.pack(fill='both', expand=True, pady=(0, 20))
        
        self.workout_text = scrolledtext.ScrolledText(
            display_container, 
            height=18,
            wrap=tk.WORD,
            font=('Consolas', 11),
            bg='#fff3e0',
            fg='#2c3e50',
            relief='flat',
            borderwidth=0,
            padx=15,
            pady=15
        )
        self.workout_text.pack(fill='both', expand=True, padx=3, pady=3)

        # Colorful button
        button_frame = tk.Frame(self.workout_tab, bg='white')
        button_frame.pack(fill='x')
        
        self.workout_button = ttk.Button(button_frame, text="🎯 Generate My Workout Plan", 
                                        command=self.generate_workout, style="Primary.TButton")
        self.workout_button.pack()

    def generate_workout(self):
        """Generate workout plan with loading state"""
        c.execute("SELECT * FROM user_profile LIMIT 1")
        profile = c.fetchone()
        if not profile:
            messagebox.showerror("Missing Profile", "⚠️ Please complete your profile first in the Profile tab!")
            return

        self.workout_button.config(state='disabled', text="🔄 Generating Your Plan...")
        self.status_var.set("🏋️ Creating your personalized workout plan...")
        
        def generate_in_thread():
            prompt = f"User: {profile[1]}, Age: {profile[2]}, Gender: {profile[3]}, Height: {profile[4]}cm, Weight: {profile[5]}kg, Goal: {profile[6]}, Daily Time: {profile[7]} min. Generate a detailed weekly workout plan with specific exercises, sets, reps, rest periods, and progression tips."
            response = query_llm(prompt)
            
            self.root.after(0, lambda: self.update_workout_display(response))
        
        threading.Thread(target=generate_in_thread, daemon=True).start()

    def update_workout_display(self, response):
        """Update workout display in main thread"""
        self.workout_text.delete('1.0', tk.END)
        self.workout_text.insert(tk.END, "🏋️ YOUR PERSONALIZED WORKOUT PLAN 🏋️\n" + "="*50 + "\n\n" + response)
        self.workout_button.config

# --- Start GUI ---
if __name__ == '__main__':
    root = tk.Tk()
    app = FitnessApp(root)
    root.mainloop()

