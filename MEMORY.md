# Jarvis Project Memory

This file tracks the development progress, decisions, and future plans for the Jarvis AI assistant project.

## Project Timeline

### Phase 1: Core Functionality (Completed)

- [x] Set up project structure
- [x] Create configuration system
- [x] Implement OpenAI API integration
- [x] Build basic command execution
- [x] Create conversation memory storage
- [x] Implement text-based interface
- [x] Test core functionality with various commands
- [x] Optimize prompt engineering

### Phase 2: Desktop UI Application (Current)

- [x] Design minimalist voice-first UI (planning completed)
- [x] Create basic PySide6 application framework 
- [x] Implement floating orb interface
- [x] Develop adaptive contextual display panels
- [x] Create settings panel with API usage tracking
- [x] Implement optimized, Iron Man-inspired orb design
- [x] Fix UI visibility and transparency issues for macOS
- [x] Implement Activity Log panel for interaction history
- [x] Implement System Monitor panel for system resource monitoring
- [ ] Implement multi-monitor support
- [ ] Create desktop application installer

### Phase 3: Voice Integration (In Progress)

- [x] Create voice manager infrastructure
- [x] Implement production speech-to-text with Whisper API
- [x] Create speech module architecture with VoiceManager, WhisperService, and TTSService
- [x] Design unified VoiceSystem service for coordinating voice components
- [x] Implement Qt-based voice controller for desktop integration
- [x] Create voice panel UI for testing and configuration
- [x] Develop test applications for speech and TTS functionality
- [x] Implement wake word detection using Porcupine
- [x] Integrate wake word detection with voice system
- [x] Create UI controls for wake word configuration
- [ ] Test voice command loop
- [ ] Optimize for sub-2 second response time

### Phase 4: Context Awareness (In Progress)

- [x] Implement screen capture functionality with mss
- [x] Add Tesseract OCR for text extraction from screen
- [x] Create context manager for centralized context handling
- [x] Implement toggle mechanism for screen observation (Start/Stop watching)
- [x] Add command for viewing current screen context
- [x] Develop application context awareness using macOS APIs
- [ ] Create personalized responses based on usage patterns

### Phase 5: Self-Hosted Brain (In Progress)

- [x] Implement service-oriented architecture with ApplicationController
- [x] Create centralized ModelManager for managing AI models
- [x] Implement SettingsManager with feature toggles
- [x] Add Ollama integration for local LLM hosting
- [x] Create unified language model interface for both local and cloud models
- [x] Add auto-launch capability for macOS
- [x] Implement FAISS vector database with sentence-transformers
- [x] Create vector-based semantic search for conversation memory
- [x] Develop enhanced context retrieval for conversations
- [x] Set up LangChain for tool integration and function calling
- [ ] Integrate GPT4All with LocalDocs feature for document processing
- [ ] Implement quantization for optimal performance
- [ ] Develop parallel processing with asyncio/multiprocessing
- [ ] Create on-demand resource loading system
- [ ] Test and optimize memory usage for MacBook Pro hardware

## Key Decisions

- **Original Base API**: OpenAI's GPT-4 for its function calling capabilities and reasoning
- **New Core Model**: GPT4All with LocalDocs for local deployment, RAG integration, and screen content analysis
- **Architecture**: Service-oriented with centralized application controller
- **Storage**: Enhanced vector database (FAISS) for conversation memory and context retrieval
- **Command Execution**: Permission-based system using LangChain for tool integration
- **Development Approach**: Incremental development with testable milestones
- **UI Design**: Voice-first with adaptive contextual text display, minimalist floating orb interface
- **Desktop Framework**: PySide6 (Qt) for cross-platform compatibility and Python integration
- **Speech-to-Text**: Local Whisper models optimized for Apple Silicon
- **Text-to-Speech**: Coqui TTS for high-quality, customizable voices running locally

## Architecture Implementation (New)

We have implemented the core architecture for Jarvis with the following components:

1. **Application Controller**: Central orchestrator for all services
   - Manages service lifecycle (start/stop)
   - Resolves service dependencies
   - Handles graceful shutdown

2. **Model Manager**: Centralized AI model management
   - Dynamic model loading/unloading based on memory constraints
   - Resource monitoring and optimization
   - Priority-based model queue

3. **Settings Manager**: User preferences and feature toggles
   - Toggle individual components (LLM, speech, TTS, etc.)
   - Persistent settings storage
   - Feature dependency resolution

4. **Ollama Service**: Integration with local language models
   - Auto-detection and startup of Ollama
   - Model pulling and management
   - Streaming text generation

5. **Language Model Service**: Unified interface for LLMs
   - Seamless switching between local and cloud models
   - Consistent API for text generation
   - Fallback strategies

6. **Auto-Launch**: System integration for startup
   - LaunchAgent creation for macOS
   - Hidden startup option
   - Configurable through settings

7. **Memory System**:
   - Vector-based storage using FAISS and sentence-transformers
   - Semantic search for finding relevant past conversations
   - Context retrieval for enhancing prompts with relevant history
   - Combined traditional and vector storage for reliability

## Desktop UI Implementation

We have implemented the initial version of the desktop UI with the following components:

1. **Main Application**: The entry point and coordinator for all UI components
2. **Floating Orb**: A draggable, always-on-top circular button that changes appearance based on state
   - Redesigned with Iron Man arc reactor aesthetic
   - Improved visibility and transparency settings
   - Enhanced draggable functionality for better placement
   - Custom shape masking for perfect circular appearance
3. **Response Panel**: Contextual panels that appear when needed with adaptive duration
4. **Settings Panel**: Configuration UI with general settings, voice settings, API settings, and usage tracking
5. **Voice Manager**: Handles voice recognition using OpenAI's Whisper API
6. **Activity Log Panel**: Displays a history of user interactions and assistant actions
   - Shows user inputs (both voice and text)
   - Records actions taken by the assistant
   - Provides filtering and search capabilities
   - Allows exporting logs for troubleshooting
   - Includes system resource monitoring
7. **System Monitor Panel**: Real-time monitoring of system resources
   - CPU usage graph with real-time updates
   - Memory usage tracking with visual representation
   - Detailed system information display
   - Integration with the Activity Log panel

Planned UI enhancements:
1. **Multi-Monitor Support**: Detecting and managing orb position across multiple displays
2. **Desktop Application Installer**: Package the application for easy installation on macOS

All components communicate via Qt signals and slots, and settings are persistently stored using QSettings.

## Voice Implementation Details

Our voice integration includes:
1. **Audio Capture**: Using PyAudio to record from the system microphone
2. **Voice Activity Detection**: Basic implementation that detects silence to determine when speaking has ended
3. **Speech-to-Text**: Currently using OpenAI's Whisper API, migrating to local Whisper models
4. **Text-to-Speech**: Planned integration with Coqui TTS for natural speech output

## Memory Implementation

We've implemented an enhanced memory system with the following components:

1. **Vector Store**:
   - FAISS-based vector database for semantic search
   - Sentence Transformers for high-quality embeddings
   - Efficient similarity search for finding relevant conversations
   - Metadata storage for context information

2. **Memory Manager**:
   - Combined traditional and vector-based storage
   - Smart context retrieval based on query relevance
   - Conversation history tracking with metadata
   - Fallback mechanisms for reliability

3. **Context Enhancement**:
   - Dynamic system prompt generation with relevant history
   - Formatted context inclusion for LLM consumption
   - Relevance scoring for prioritizing important memories
   - Efficient storage and retrieval patterns

## LangChain Integration

We've implemented a comprehensive LangChain integration system to provide tool calling capabilities with local models:

### LangChain Service Architecture
- **Central Service**: `jarvis/brain/langchain_service.py` provides the core functionality
- **Tool Registration**: Dynamic registration of tools with name, function, and description
- **Model Integration**: Compatible with both local models (Ollama) and cloud models (OpenAI)
- **Agent Framework**: Uses LangChain's agent capabilities for reasoning and tool selection

### Tool Categories
We've implemented several tool categories for different functionalities:

1. **System Tools**:
   - System information retrieval
   - Safe command execution
   - Environment variable access
   - Process monitoring and management

2. **File Tools**:
   - Directory browsing and listing
   - File reading with safety limits
   - File writing with security checks
   - File searching and pattern matching

3. **Web Tools**:
   - Web page content extraction
   - Search capabilities via DuckDuckGo
   - Weather information retrieval

### Integration with Context Awareness
The LangChain tools can utilize the context awareness system to:
- Process screen content for information extraction
- Use application context for relevant actions
- Enhance responses with environmental awareness

### Next Steps for LangChain Integration
- Add more specialized tools for specific domains
- Implement chain-of-thought reasoning for complex tasks
- Create structured output parsers for consistent results
- Add tool-specific memory for context continuity

## Self-Hosted Models Research

Based on thorough analysis, we're shifting to a fully local deployment approach:

### Language Model Selection
- **GPT4All**: Best choice for our use case with strong document processing capabilities
  - Supports over 1,000 models (including Llama and Mistral)
  - Built-in LocalDocs feature for RAG integration and context awareness
  - Python bindings for seamless integration
  - Optimized for Apple Silicon with Core ML conversion options
  - Requires ~10-14GB RAM when quantized to 4-bit or 8-bit precision

### Speech Recognition
- **Open-source Whisper**: The tiny model (~500MB) offers excellent performance
  - Leverages MacBook Pro's Neural Engine for fast transcription
  - Local execution eliminates API costs and latency
  - High accuracy for speech-to-text in quiet environments

### Text-to-Speech
- **Coqui TTS**: Lightweight (~1-2GB RAM) with customizable voices
  - Support for streaming audio output for immediate response
  - Voice cloning capabilities for personalization
  - Local deployment with no latency or API costs

### Memory Storage
- **FAISS with sentence-transformers**: Optimal for storing conversation history
  - Fast similarity search (~1GB RAM for moderate datasets)
  - Enables context-aware recall and personalization
  - Fully local operation with no cloud dependencies

### Screen Capture & Analysis
- **pyscreenshot/mss**: Lightweight tools for capturing screenshots on demand
- **Tesseract OCR**: Accurate text extraction with minimal resource usage (~1-2GB RAM)
- **OpenCV-Python**: For image comparison to detect significant screen changes

### Tool Integration
- **LangChain**: Best framework for enabling tool-calling capabilities
  - Seamless integration with GPT4All
  - Low overhead for defining and calling tools
  - Python-native for easy extensibility

## Implementation Plan (Updated)

The updated implementation plan takes advantage of MacBook Pro M4 capabilities while ensuring real-time responsiveness:

### Phase 1: Memory and Personality Enhancement (Completed)
1. ✅ Implement FAISS with sentence-transformers for vector storage
2. ✅ Create system prompt for consistent Jarvis personality
3. ✅ Add context retrieval system to include relevant past interactions

### Phase 2: Screen Viewing Implementation (Next)
1. Add screenshot capture with pyscreenshot/mss
2. Implement Tesseract OCR for text extraction
3. Create toggle commands for starting/stopping screen observation
4. Develop change detection to process screenshots only when needed

### Phase 3: Local Model Deployment
1. Install GPT4All using Ollama for simplified deployment
2. Set up model quantization for optimal performance
3. Replace OpenAI function calls with LangChain for tool integration
4. Test and optimize response generation time

### Phase 4: Voice System Enhancement
1. Migrate from Whisper API to local Whisper models
2. Implement Coqui TTS with streaming capability
3. Add parallel processing for simultaneous listening and speaking
4. Optimize for latency and responsive interaction

### Phase 5: Performance Optimization
1. Implement on-demand resource loading
2. Add memory usage monitoring and adjustment
3. Convert models to Core ML format where applicable
4. Set up resource-efficient parallel processing

## Next Steps (Immediate Priority)

1. Complete screen capture and observation feature
2. Integrate fully with Ollama for local language models
3. Migrate fully to local Whisper models (tiny/base) for speech recognition
4. Optimize TTS with Coqui voice models for natural sounding responses
5. Complete integration with main application flow for voice-first interaction

## Recent Implementation: Memory System and UI Refinements

We have implemented the following components:

1. **Vector-Based Memory**:
   - FAISS vector database implementation for semantic search
   - Integration with sentence-transformers for high-quality embeddings
   - Memory manager that combines traditional and vector storage
   - Context retrieval system for relevant conversation history

2. **UI Improvements**:
   - Enhanced floating orb with Iron Man arc reactor design
   - Fixed macOS visibility and transparency issues
   - Improved dragging and positioning capabilities
   - Added automatic centering and raise-to-top functionality

3. **Testing**:
   - Created test scripts for the vector memory components
   - Developed UI test applications for the simplified orb
   - Fixed cross-platform compatibility issues

## Recent Technical Decisions

1. **Memory System**: Implemented FAISS with sentence-transformers for:
   - Efficient semantic search capabilities
   - Low memory footprint (~1GB for moderate history)
   - Fast retrieval of relevant context
   - Metadata storage for enhanced context

2. **UI Design**: Made key improvements to the orb interface:
   - Used circular window masking for perfect shape
   - Implemented custom paint events for visual styling
   - Added window flags for proper display on macOS
   - Created simplified fallback designs for compatibility

3. **Wake Word Detection**: Selected Porcupine by Picovoice for its:
   - Lightweight resource usage (ideal for background operation)
   - Customizable sensitivity and wake words
   - Low false positive/negative rates
   - Cross-platform compatibility

4. **Speech Recognition**: Using a dual approach with both OpenAI Whisper API and local Whisper models
   - API for initial development and faster iterations
   - Local models for privacy and offline functionality

5. **Text-to-Speech**: Selected Coqui TTS over ElevenLabs for local deployment benefits
   - Complete offline operation
   - Multiple voices with reasonable quality
   - Significantly lower resource usage

## Resource Management

Optimizing for MacBook Pro M4 with 24GB memory:
- GPT4All (quantized): ~7-9GB (keep loaded)
- Whisper Tiny: ~500MB (load on-demand)
- Tesseract OCR: ~1-2GB (load on-demand)
- Coqui TTS: ~1-2GB (load on-demand)
- FAISS: ~1GB (keep loaded for quick recall)
- Total peak usage: ~12-14GB, leaving ~10GB for macOS and other applications

## Known Issues

- Basic voice activity detection may not work well in noisy environments
- Need to implement actual API cost tracking based on tokens (until fully migrated to local models)
- Settings panel for startup at login requires platform-specific implementation
- Response panel positioning needs refinement for various screen configurations
- Screen observation may increase CPU/GPU usage and impact battery life

## Recent Updates (March 19, 2025)

We've made significant progress on improving the desktop UI and monitoring capabilities:

1. **Activity Log Panel Implementation**:
   - Created a comprehensive logging system for user interactions
   - Built a tabbed interface with filtering capabilities
   - Added export functionality for troubleshooting
   - Implemented clear categorization of log entries (user, assistant, system, action)
   
2. **System Monitor Integration**:
   - Added real-time CPU and memory usage monitoring
   - Created visual graphs with time-series data
   - Built detailed system information displays with key metrics
   - Integrated system monitoring within the Activity Log panel interface
   
3. **UI Visibility Enhancements**:
   - Fixed issues with orb positioning going off-screen
   - Ensured proper on-screen detection and positioning
   - Improved menu bar icon visibility with high-contrast design
   - Added robust visibility status checking and logging
   
4. **Menu Bar Integration**:
   - Enhanced menu bar icon implementation
   - Created consistent styling across application icons
   - Fixed visibility issues on macOS Sonoma
   - Improved icon contrast for better visibility
   
5. **Stability Improvements**:
   - Added extensive logging for better troubleshooting
   - Enhanced error handling in screen capture and OCR modules
   - Improved reliability of position saving and restoration
   - Fixed issues with application startup and visibility

Next immediate steps:
- Complete testing of voice command loop
- Integrate local Whisper model for speech recognition
- Implement Coqui TTS for text-to-speech
- Test OCR capabilities with Tesseract once installed
- Begin implementation of GPT4All with LocalDocs