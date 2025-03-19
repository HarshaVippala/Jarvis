# Jarvis - Personal AI Assistant

<p align="center">
  <img src="jarvis/jarvis.PNG" alt="Jarvis Logo" width="200"/>
</p>

Jarvis is an advanced personal AI assistant built in Python with natural language processing capabilities, voice recognition, and a desktop interface. Inspired by Iron Man's AI companion, Jarvis helps you interact with your computer, access information, and perform tasks using natural language.

## Features

- **Voice Interaction**: Wake word detection and voice command processing
- **Natural Language Processing**: Understanding and responding to queries
- **Memory System**: Persistent storage of conversations and contexts
- **Desktop Interface**: Modern UI with floating orb and conversation panels
- **System Monitoring**: Track system performance and resource usage
- **Activity Logs**: Keep track of all interactions with the assistant
- **Vector Memory**: FAISS-powered semantic memory for contextual understanding
- **Local Model Support**: Integration with Ollama for local LLM capabilities
- **Tool Integration**: Execute system commands and access external services

## Architecture

Jarvis is built with a modular architecture:

- **Core**: Central controller for the assistant
- **Brain**: Language processing and reasoning components
- **Speech**: Voice recognition and synthesis
- **Memory**: Storage and retrieval systems
- **Desktop**: UI components and interaction
- **Tools**: Utility modules for various tasks

## Requirements

- Python 3.9+
- PySide6 for desktop UI
- PyTorch for machine learning components
- Various audio processing libraries
- FAISS for vector storage
- OpenAI API key (optional)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/HarshaVippala/Jarvis.git
   cd Jarvis
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r desktop_requirements.txt
   ```

3. Set up environment variables (copy `.env.example` to `.env` and fill in your API keys)

## Usage

Start the desktop application:

```bash
python jarvis/start_desktop.py
```

### Voice Commands

Activate Jarvis with the wake word "Hey Jarvis" and then speak your command. For example:
- "Hey Jarvis, what time is it?"
- "Hey Jarvis, open Settings"
- "Hey Jarvis, search for the latest news"

### Desktop Interface

The desktop interface features:
- **Floating Orb**: Main interaction point, click to activate
- **Response Panel**: Displays Jarvis's responses
- **Activity Log**: Shows interaction history
- **System Monitor**: Displays resource usage

## Project Structure

```
jarvis/
├── brain/         # NLP and reasoning components
├── core/          # Core application logic
├── desktop/       # Desktop UI components
├── memory/        # Storage and retrieval systems
├── speech/        # Voice interaction components
├── tools/         # Utility modules
└── config/        # Configuration files
```

## Advanced Configuration

Jarvis can be customized by modifying settings in the `.env` file:

```
# API Keys
OPENAI_API_KEY=your_api_key_here

# Voice Settings
TTS_PROVIDER=system  # Options: system, elevenlabs
WAKE_WORD_SENSITIVITY=0.7

# Model Settings
DEFAULT_MODEL=gpt-4
USE_LOCAL_MODELS=true
```

## Troubleshooting

Common issues:
- **Voice recognition not working**: Ensure microphone permissions are granted
- **High memory usage**: Adjust local model settings or disable vector memory
- **Slow responses**: Check internet connection or switch to a lighter model

## Contributing

Contributions are welcome! Feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Created by [Harsha Vippala](https://github.com/HarshaVippala) 