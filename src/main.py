import speech_recognition as sr
from gtts import gTTS
import os
import pygame
from langchain_ollama import OllamaLLM
import signal
import sys
import time

class AudioChatbot:
    def __init__(self, model_name="llama2"):
        print(f"\nInitializing chatbot with Ollama model: {model_name}")
        self.recognizer = sr.Recognizer()
        self.llm = OllamaLLM(model=model_name)
        self.is_running = True
        self.temp_file = "temp_speech.mp3"
        
        # Initialize pygame mixer
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
        """Convert speech to text"""
        try:
            with sr.Microphone() as source:
                print("\nListening... (Say 'stop' or press Ctrl+C to exit)")
                audio = self.recognizer.listen(source)
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return None

    def get_llm_response(self, text):
        """Get response from Ollama"""
        if not text:
            return "నేను మీ మాట వినలేదు. దయచేసి మళ్ళీ చెప్పండి."  # I couldn't understand. Please repeat in Telugu
        try:
            # Add system instruction for brief responses
            prompt = ("System: Keep your responses short, clear, and to-the-point. Avoid over-explaining. Always return the responses in Telugu language \n"
                     f"User: {text}")
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return "ఏదో తప్పు జరిగింది. దయచేసి మళ్ళీ ప్రయత్నించండి."  # An error occurred. Please try again in Telugu

    def speak(self, text):
        """Convert text to speech in Telugu"""
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
        
        while self.is_running:
            try:
                # Get user input through speech
                user_input = self.listen()
                if not user_input:
                    continue
                    
                # Exit conditions
                if user_input.lower() in ["quit", "exit", "bye", "stop"]:
                    self.speak("సర్లే నువ్వు వెళ్ళిరా!")  # Goodbye! Have a great day! in Telugu
                    break
                
                # Get and speak response
                response = self.get_llm_response(user_input)
                if self.is_running:  # Check if we should still speak
                    self.speak(response)
                
            except Exception as e:
                print(f"\nAn error occurred: {e}")
                break

def main():
    chatbot = AudioChatbot(model_name="llama3.2")
    chatbot.run()

if __name__ == "__main__":
    main()