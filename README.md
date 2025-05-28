# Jarvis - Personal AI Assistant

<p align="center">
  <img src="jarvis.PNG" alt="Jarvis Logo" width="200"/>
</p>

Jarvis is an ambitious personal AI assistant project still in its early stages. Heavily inspired by Tony Stark's J.A.R.V.I.S. from Iron Man, this is my attempt to build a Jarvis myself from scratch. Most features are still being developed and are not yet fully functional, but I'm actively working on building this step by step.

I built Jarvis as a prototype for what I believe personal AI will evolve into—something as ubiquitous and personalized as the iPhone is today. The vision is that in the near future, each person will own a truly personal AI assistant whose “brain” (the core LLM handling reasoning and interaction) can be swapped or upgraded just like a phone, while the “memory” (context, preferences, emotional history, and behavioral patterns) remains securely theirs. This memory would be stored locally, either on-device or in a secure "cold-storage" like module so privacy and continuity are preserved even when the model changes. I used Python to build the orchestration layer, OpenAI APIs to prototype the language model backend, and designed the memory system to use local JSON files with future support planned for on-device vector stores like SQLite with pgvector or ChromaDB. For voice interaction, I integrated Whisper for real-time transcription and scoped out open-source TTS solutions like Coqui and Piper for generating responses. Each component—speech, memory, model, and task handling—was modular, making it easy to swap models, enhance capabilities, or even run fully offline in the future.

The current version supports voice input, memory persistence, and contextual conversation management using a decoupled architecture. Future versions aim to introduce autonomous scheduling, emotional context awareness, proactive reminders, and the ability to trigger custom actions like sending messages, managing daily routines, or interacting with apps. I also plan to support model-agnostic integration, enabling seamless switching between open-weight models and proprietary APIs depending on user preference and device capability. The assistant is envisioned to not only respond when spoken to but also to understand when to initiate interaction, when to stay silent, and how to adjust its behavior based on the user’s emotional cues or habits over time (long long stretch - hopefully using future models that can combine emotion, behavior, intent—designed and light enough to run on mobile or edge devices) .

## Technologies Used

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PyTorch-%23EE4C2C.svg?style=for-the-badge&logo=PyTorch&logoColor=white" alt="PyTorch">
  <img src="https://img.shields.io/badge/Qt-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="Qt">
  <img src="https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI">
  <img src="https://img.shields.io/badge/FAISS-FB4D6C?style=for-the-badge&logo=meta&logoColor=white" alt="FAISS">
  <img src="https://img.shields.io/badge/Ollama-00A8E1?style=for-the-badge&logo=llama&logoColor=white" alt="Ollama">
</p>

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

## Author

Created by [Harsha Vippala](https://github.com/HarshaVippala)
