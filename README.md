# Bujji - Telugu Voice Assistant

Bujji is an intelligent voice-based chatbot that specializes in Telugu language interaction. It combines state-of-the-art speech recognition, natural language processing, and text-to-speech capabilities to provide a seamless conversational experience in Telugu.

## Features

### Voice Interaction
- Bilingual speech recognition (Telugu and English fallback)
- Natural Telugu text-to-speech using gTTS
- 6-second voice input duration
- Real-time audio feedback and status indicators

### Smart Conversations
- Powered by Google's Gemini 2.0 Flash LLM
- Context-aware responses using LangChain
- Maintains conversation history for personalized interactions
- Warm and friendly Telugu language responses

### User Management
- Secure user authentication system
- Password encryption using bcrypt
- Multi-user support with individual conversation histories
- Persistent conversation storage using ChromaDB

### Modern GUI
- Clean and intuitive Tkinter-based interface
- Real-time conversation display
- Visual recording and playback controls
- Status indicators for system feedback

### Technical Features
- Asynchronous Audio Processing
  - Parallel speech recognition and text-to-speech processing using threading
  - Non-blocking GUI updates during audio operations
  - Background audio recording with configurable time limits (6-second default)
  - Graceful interruption handling for both recording and playback
  - Thread-safe state management for recording and speaking states
  - Automatic cleanup of temporary audio files

- Thread-safe Operations
  - Separate threads for audio recording and playback
  - Safe GUI updates from background threads
  - Protected shared resource access
  - Proper thread termination on application exit

- Error Handling
  - Graceful fallback from Telugu to English speech recognition
  - Recovery from network interruptions
  - Proper resource cleanup
  - User-friendly error messages

- Cross-platform Compatibility
  - Consistent audio handling across operating systems
  - Platform-independent GUI using Tkinter
  - Portable file operations

## Prerequisites

- Python 3.8 or higher
- A Google API key for Gemini LLM
- Microphone access for voice input
- Speakers for audio output

## Getting Started

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Bujji.git
cd Bujji
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your Google API key:
Create a .env file in the project root and add:
```
GOOGLE_API_KEY=your_api_key_here
```

5. Run the project:
```bash
python src/main.py
```

## Usage

1. Register/Login with your credentials
2. Click the microphone button to start speaking
3. Speak in Telugu (or English if Telugu recognition fails)
4. Listen to Bujji's response
5. Use the stop button to interrupt any ongoing interaction

## Exit Commands

You can end the conversation using any of these commands:
- English: "quit", "exit", "bye", "stop"
- Telugu: "ఆపు", "సరే", "చాలు", "వెళ్తున్నా"

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.