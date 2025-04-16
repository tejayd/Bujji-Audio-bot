import speech_recognition as sr
from gtts import gTTS
import os
import pygame
import google.generativeai as genai
from dotenv import load_dotenv
import signal
import sys
import time

class AudioChatbot:
    def __init__(self, model_name="gemini-2.0-flash"):
        print(f"\nInitializing chatbot with Gemini model: {model_name}")
        # Load environment variables
        load_dotenv()
        
        # Configure Gemini
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Please set GOOGLE_API_KEY in your .env file")
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(model_name)
        self.chat = self.model.start_chat(history=[])
        
        # Initialize other components
        self.recognizer = sr.Recognizer()
        self.is_running = True
        self.temp_file = "temp_speech.mp3"
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def __del__(self):
        # Clean up temporary file
        if os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass
        pygame.mixer.quit()

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\nGracefully shutting down... (Press Ctrl+C again to force quit)")
        self.is_running = False
        
    def listen(self):
        """Convert speech to text with Telugu support"""
        try:
            with sr.Microphone() as source:
                print("\nListening... (చెప్పండి 'ఆపు' లేదా Ctrl+C to exit)")
                audio = self.recognizer.listen(source)
                # Try Telugu first, then English if Telugu fails
                try:
                    text = self.recognizer.recognize_google(audio, language="te-IN")
                    print(f"మీరు చెప్పారు: {text}")
                except:
                    # Fallback to English if Telugu recognition fails
                    text = self.recognizer.recognize_google(audio, language="en-US")
                    print(f"You said: {text}")
                return text
        except sr.UnknownValueError:
            print("మాట వినబడలేదు / Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"గుర్తింపు సేవలో లోపం / Recognition service error; {e}")
            return None

    def get_llm_response(self, text):
        """Get response from Gemini"""
        if not text:
            return "నేను మీ మాట వినలేదు. దయచేసి మళ్ళీ చెప్పండి."  # I couldn't understand. Please repeat in Telugu
        try:
            # Add system instruction for brief responses in Telugu
            prompt = ("Keep your responses short, clear, and to-the-point. Always respond in Telugu language. Here's the user's input: " + text)
            response = self.chat.send_message(prompt)
            return response.text
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return "ఏదో తప్పు జరిగింది. దయచేసి మళ్ళీ ప్రయత్నించండి."  # An error occurred. Please try again in Telugu

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
    chatbot = AudioChatbot()  
    chatbot.run()

if __name__ == "__main__":
    main()