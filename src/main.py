import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import speech_recognition as sr
from gtts import gTTS
import pygame
import google.generativeai as genai
from dotenv import load_dotenv
import signal
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
from user_manager import UserManager

from langchain_google_genai import GoogleGenerativeAI
from langchain.chains import create_history_aware_retriever
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import HumanMessage, AIMessage
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.runnables import RunnableConfig
from langchain_core.output_parsers import StrOutputParser

class LoginWindow:
    def __init__(self, on_login_success):
        self.window = tk.Tk()
        self.window.title("Bujji Login")
        self.window.geometry("500x500")
        self.user_manager = UserManager()
        self.on_login_success = on_login_success
        
        # Username
        ttk.Label(self.window, text="Username:").pack(pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(self.window, textvariable=self.username_var).pack()
        
        # Password
        ttk.Label(self.window, text="Password:").pack(pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(self.window, textvariable=self.password_var, show="*").pack()
        
        # Login button
        ttk.Button(self.window, text="Login", command=self.login).pack(pady=10)
        ttk.Button(self.window, text="Register", command=self.register).pack()
        
        self.window.mainloop()
    
    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        
        if self.user_manager.authenticate(username, password):
            context = self.user_manager.get_user_context(username)
            self.window.destroy()
            self.on_login_success(username, context)
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def register(self):
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        if self.user_manager.create_user(username, password):
            messagebox.showinfo("Success", "User registered successfully! You can now login.")
        else:
            messagebox.showerror("Error", "Username already exists")

class AudioChatbotGUI:
    def __init__(self, root, username, user_context):
        self.root = root
        self.root.title(f"Bujji - Telugu Chatbot - User: {username}")
        self.root.geometry("400x600")
        
        self.username = username
        self.user_context = user_context
        self.user_manager = UserManager()
        
        # Initialize the chatbot with full context
        self.chatbot = AudioChatbot(user_context)
        self.is_recording = False
        self.is_speaking = False
        
        # Create GUI elements
        self.setup_gui()
        
        # Welcome message without showing previous context
        welcome_msg = f"నమస్కారం {username}!"
        self.add_bot_message(welcome_msg)
        # Store welcome message in context
        self.user_manager.update_user_context(self.username, welcome_msg, is_human=False)
        self.chatbot.speak(welcome_msg)
    
    def setup_gui(self):
        # Chat display area
        self.chat_frame = ttk.Frame(self.root)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Chat display
        self.chat_display = tk.Text(self.chat_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_label = ttk.Label(self.root, text="Ready")
        self.status_label.pack(pady=5)
        
        # Microphone button
        self.mic_button = ttk.Button(
            self.root,
            text="🎤 Press to Speak",
            command=self.toggle_recording
        )
        self.mic_button.pack(pady=10, padx=20, fill=tk.X)
        
        # Stop button
        self.stop_button = ttk.Button(
            self.root,
            text="⏹ Stop",
            command=self.stop_interaction
        )
        self.stop_button.pack(pady=(0, 10), padx=20, fill=tk.X)
    
    def add_user_message(self, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"You: {message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def add_bot_message(self, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"Bujji: {message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def toggle_recording(self):
        if self.is_speaking:
            # Stop current speech if any
            pygame.mixer.music.stop()
            self.is_speaking = False
        
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        self.is_recording = True
        self.mic_button.config(text="🔴 Recording...")
        self.status_label.config(text="Listening...")
        
        # Start recording in a separate thread
        threading.Thread(target=self.record_audio, daemon=True).start()
    
    def stop_recording(self):
        self.is_recording = False
        self.mic_button.config(text="🎤 Press to Speak")
        self.status_label.config(text="Processing...")
    
    def record_audio(self):
        try:
            text = self.chatbot.listen()
            if text:
                self.add_user_message(text)
                
                # Process in separate thread to keep GUI responsive
                threading.Thread(target=self.process_input, args=(text,), daemon=True).start()
            else:
                self.status_label.config(text="Could not understand audio")
                
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
        finally:
            self.is_recording = False
            self.mic_button.config(text="🎤 Press to Speak")
    
    def process_input(self, text):
        if text.lower() in ["quit", "exit", "bye", "stop", "ఆపు", "సరే", "చాలు", "వెళ్తున్నా"]:
            response = "సర్లే నువ్వు వెళ్ళి రా!"
            self.add_bot_message(response)
            self.speak_response(response)
            self.root.after(2000, self.root.quit)
        else:
            # Update user context with the user's message
            self.user_manager.update_user_context(self.username, text, is_human=True)
            
            # Get bot response
            response = self.chatbot.get_llm_response(text)
            
            # Update user context with bot's response
            self.user_manager.update_user_context(self.username, response, is_human=False)
            
            self.add_bot_message(response)
            self.speak_response(response)
    
    def speak_response(self, text):
        self.is_speaking = True
        self.status_label.config(text="Speaking...")
        
        try:
            # Create gTTS object with Telugu language
            tts = gTTS(text=text, lang='te')
            
            # Save the audio
            tts.save(self.chatbot.temp_file)
            
            # Play audio using pygame
            pygame.mixer.music.load(self.chatbot.temp_file)
            pygame.mixer.music.play()
            
            # Wait for audio to finish
            while pygame.mixer.music.get_busy() and self.is_speaking:
                time.sleep(0.1)
            
            # Clean up
            if os.path.exists(self.chatbot.temp_file):
                os.remove(self.chatbot.temp_file)
                
        except Exception as e:
            self.status_label.config(text=f"Error in speech: {str(e)}")
        finally:
            self.is_speaking = False
            self.status_label.config(text="Ready")
    
    def stop_interaction(self):
        if self.is_speaking:
            self.is_speaking = False
            pygame.mixer.music.stop()
        if self.is_recording:
            self.is_recording = False
        self.status_label.config(text="Ready")
        self.mic_button.config(text="🎤 Press to Speak")

class AudioChatbot:
    def __init__(self, user_context=None):
        print(f"\nInitializing chatbot with user context...")
        load_dotenv()
        
        # Configure LangChain with Gemini
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Please set GOOGLE_API_KEY in your .env file")
            
        self.llm = GoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.7
        )
        
        # Set up conversation template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Telugu speaking chatbot named Bujji. Your responses should be warm, friendly and in Telugu language."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}")
        ])
        
        # Initialize context and chat history
        self.chat_history = []
        if user_context and user_context.get("history"):
            context_str = "\n".join(user_context["history"][-5:])
            self.chat_history.append(HumanMessage(content="Previous context: " + context_str))
            self.chat_history.append(AIMessage(content="నేను అర్థం చేసుకున్నాను. మీరు ఏమి చెప్పాలనుకుంటున్నారు?"))
        
        # Setup chain
        self.chain = (
            {"input": RunnablePassthrough(), "chat_history": lambda _: self.chat_history}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        # Initialize other components
        self.recognizer = sr.Recognizer()
        self.is_running = True
        self.temp_file = "temp_speech.mp3"
        pygame.mixer.init()
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\nGracefully shutting down... (Press Ctrl+C again to force quit)")
        self.is_running = False
        
    def listen(self):
        """Convert speech to text with Telugu support"""
        try:
            with sr.Microphone() as source:
                # Add a longer phrase time limit (default is 3 seconds, so 6 seconds now)
                audio = self.recognizer.listen(source, phrase_time_limit=6.0)
                # Try Telugu first, then English if Telugu fails
                try:
                    text = self.recognizer.recognize_google(audio, language="te-IN")
                except:
                    # Fallback to English if Telugu recognition fails
                    text = self.recognizer.recognize_google(audio, language="en-US")
                return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            raise Exception(f"Recognition service error: {e}")

    def get_llm_response(self, text):
        """Get response using LangChain conversation chain"""
        if not text:
            return "నేను మీ మాట వినలేదు. దయచేసి మళ్ళీ చెప్పండి."
        try:
            response = self.chain.invoke(text)
            
            # Update chat history
            self.chat_history.extend([
                HumanMessage(content=text),
                AIMessage(content=response)
            ])
            
            # Keep only last 10 messages
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]
                
            return response
            
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return "ఏదో తప్పు జరిగింది. దయచేసి మళ్ళీ ప్రయత్నించండి."

    def speak(self, text):
        """Convert text to speech using gTTS for Telugu"""
        print(f"Bot: {text}")
        try:
            # Create gTTS object with Telugu language
            tts = gTTS(text=text, lang='te')
            
            # Save the audio
            tts.save(self.temp_file)
            
            # Play audio using pygame
            pygame.mixer.music.load(self.temp_file)
            pygame.mixer.music.play()
            
            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                if not self.is_running:
                    pygame.mixer.music.stop()
                    break
                
            # Clean up
            if os.path.exists(self.temp_file):
                os.remove(self.temp_file)
                
        except Exception as e:
            print(f"Error in text-to-speech: {e}")

    def run(self):
        """Main chat loop"""
        print("Chatbot initialized. Say something or 'stop' to exit. Press Ctrl+C for graceful shutdown.")
        
        # Initial Telugu greeting
        welcome_msg = "ఏరా ఎలా ఉన్నావ్, నా పేరు బుజ్జి, ఏం కావాలి నీకు"  # Hello! I am your friend. How can I help you?
        self.speak(welcome_msg)
        
        while self.is_running:
            try:
                # Get user input through speech
                user_input = self.listen()
                if not user_input:
                    continue
                    
                # Exit conditions
                if user_input.lower() in ["quit", "exit", "bye", "stop", "ఆపు", "సరే", "చాలు", "వెళ్తున్నా"]:
                    self.speak("సర్లే నువ్వు వెళ్ళి రా!")  # Goodbye! Have a great day! in Telugu
                    break
                
                # Get and speak response
                response = self.get_llm_response(user_input)
                if self.is_running:  # Check if we should still speak
                    self.speak(response)
                
            except Exception as e:
                print(f"\nAn error occurred: {e}")
                break

def main():
    def on_login_success(username, context):
        root = tk.Tk()
        app = AudioChatbotGUI(root, username, context)
        root.mainloop()
    
    LoginWindow(on_login_success)

if __name__ == "__main__":
    main()