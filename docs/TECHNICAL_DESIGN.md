# Technical Design Document

This document outlines the technical architecture and design decisions for the Jarvis AI assistant.

## System Architecture

The Jarvis AI assistant is designed with a modular architecture to ensure flexibility, maintainability, and ease of component replacement. The system is built around several core components that work together to provide a seamless user experience.

```
┌─────────────────────────────────────────────────────────────────┐
│                       Jarvis AI Assistant                        │
├──────┬────────────────────────────────────────────────┬─────────┤
│      │                                                │         │
│ App  │              Service Registry                  │ Settings│
│ Ctrl │                                                │ Manager │
│      │                                                │         │
└──────┴────┬─────────────┬────────────────┬───────────┴─────────┘
            │             │                │                 
      ┌─────▼───┐   ┌─────▼────┐    ┌─────▼────┐    ┌─────────────┐
      │         │   │          │    │          │    │             │
      │ Desktop │   │  Voice   │    │ Language │    │  Context    │
      │   UI    │   │  System  │    │  Model   │    │ Awareness   │
      │         │   │          │    │          │    │             │
      └─────┬───┘   └────┬─────┘    └────┬─────┘    └─────┬───────┘
            │            │                │               │
      ┌─────▼───┐   ┌────▼────────┐ ┌────▼────────┐ ┌────▼────────┐
      │         │   │             │ │             │ │             │
      │Interface│   │  Speech     │ │  Language   │ │  Memory &   │
      │Components   │ Processing  │ │ Processing  │ │Personalizatn│
      │         │   │             │ │             │ │             │
      └─────────┘   └─────────────┘ └─────────────┘ └─────────────┘
```

## Application Controller

The Application Controller serves as the central orchestration component for Jarvis, managing the entire application lifecycle.

### Responsibilities

- **Application Lifecycle Management**: Controls startup, shutdown, and state transitions
- **Service Registration and Discovery**: Maintains registry of all services
- **Dependency Management**: Ensures services are initialized in the correct order
- **Resource Allocation**: Oversees system resource distribution across components
- **Error Handling**: Provides centralized error management and recovery

### Startup Sequence

1. **Application Launch**: Triggered by user or system startup
2. **Core Services Initialization**: UI, settings, essential utilities
3. **Background Resource Preparation**: Pre-loads frequently used resources
4. **Model Manager Initialization**: Prepares model infrastructure without loading models
5. **Service Registration**: Each component registers with the service registry
6. **UI Presentation**: Display user interface when ready

### Shutdown Sequence

1. **Save State**: Persist current state and user data
2. **Resource Release**: Clean up and release system resources
3. **Model Unloading**: Properly unload AI models
4. **Service Termination**: Gracefully terminate all services
5. **Exit Confirmation**: Log successful shutdown

## Core Components

### 1. Model Manager

The Model Manager is responsible for centralized management of all AI models used by Jarvis:

- **Unified Interface**: Provides consistent API for model access
- **Lifecycle Management**: Handles loading, unloading, and resource allocation
- **On-Demand Loading**: Initializes models only when needed
- **Resource Optimization**: Dynamically adjusts model parameters based on system load
- **Model Swapping**: Supports hot-swapping of models without application restart

### 2. Desktop UI

The Desktop UI provides a minimalist, non-intrusive interface for interacting with Jarvis.

- **Framework**: PySide6 (Qt for Python)
- **Design Approach**: Voice-first with adaptive contextual display
- **Key Components**:
  - **Floating Orb**: Always-on-top circular button with state-based appearance
  - **Response Panel**: Contextual panels with adaptive duration
  - **Settings Panel**: Configuration for general settings, voice, API usage
  - **Activity Log Panel**: History of interactions and actions (planned)

**Communication Pattern**: Uses Qt's signals and slots for component interactions, with persistent settings stored using QSettings.

### 3. Voice System

The voice system handles bidirectional audio communication with the user through a unified service.

- **Centralized Management**: Single service coordinates all voice components
- **Automatic Initialization**: Starts with application but defers model loading
- **Resource Efficiency**: Dynamically manages memory usage

Components:
- **Speech-to-Text**: Local Whisper models
  - Model Size: Tiny (~500MB)
  - Expected Latency: <1 second
  - Optimization: Core ML integration for Apple Silicon

- **Text-to-Speech**: Coqui TTS
  - Model Size: ~1-2GB
  - Voice Customization: Supports voice cloning
  - Streaming Capability: Begins playback before full generation

- **Voice Activity Detection**: Silence detection with configurable threshold

### 4. Language Model

The language model serves as the "brain" of Jarvis, understanding user intent and generating appropriate responses.

- **Core Model**: GPT4All
  - Primary Model: Mistral 7B with 4-8 bit quantization
  - Memory Usage: ~7-9GB (quantized)
  - Key Feature: LocalDocs for document processing
  - Auto-Loading: Handled by model manager at runtime

- **Tool Integration**: LangChain
  - Function Calling: Custom Python functions for system operations
  - API Integration: Weather, calendar, email, etc.
  - OS Integration: File system access, application control

### 5. Context Awareness

The context awareness system enables Jarvis to understand and respond to user's environment and history.

- **Screen Observation** (Implemented):
  - Capture Tool: mss for efficient screen capturing
  - Text Extraction: Tesseract OCR with preprocessing for enhanced extraction
  - Change Detection: OpenCV-Python with image hashing for efficient change detection
  - Toggle Mechanism: Voice commands to start/stop observation

- **Application Context** (Implemented):
  - Active Application: macOS AppleScript integration via System Events
  - Window Title: Accessibility API for active window information
  - Bundle Identifier: Application metadata for precise app identification
  - Secure Access: Proper permissions handling through macOS Security & Privacy

- **Memory Management** (Implemented):
  - Vector Database: FAISS with sentence-transformers
  - Context Window: Retrieves 5-10 relevant past interactions
  - Storage Efficiency: ~1GB for moderate history

### Tool Integration with LangChain

Jarvis now includes a comprehensive tool integration system using LangChain:

- **LangChain Service**: Central service for tool registration and agent management
  - Tool Registration: Dynamic registration of system, file, and web tools
  - Agent Creation: Uses LangChain's agent framework with local models
  - Prompt Templates: Support for templated prompts with variables

- **System Tools**:
  - System Information: Hardware, OS, memory, and CPU details
  - Command Execution: Safe shell command execution with security checks
  - Environment Variables: Access to system environment (with sensitive value masking)
  - Process Management: Monitoring of running processes

- **File Tools**:
  - Directory Listing: Browse and explore filesystem
  - File Reading: Access to text file contents with size limits
  - File Writing: Safe file creation and modification
  - File Search: Pattern-based file discovery

- **Web Tools**:
  - Web Page Retrieval: Extract content from web pages
  - Web Search: Access to information via DuckDuckGo
  - Weather Information: Basic weather lookups 

### LangChain Model Integration

The LangChain integration connects with our Ollama service:

- **Model Wrapper**: LangChain compatible wrapper for Ollama models
- **Streaming Support**: Real-time token streaming for responsive UI
- **Parameter Control**: Temperature, context size, and other model parameters
- **Context Enhancement**: Automatic inclusion of relevant context in prompts

## Service Architecture

Jarvis uses a service-oriented architecture to promote modularity and maintainability:

### Service Registry

- **Central Service Registry**: Maintains references to all active services
- **Service Discovery**: Allows components to locate required services
- **Dependency Injection**: Manages service dependencies
- **Lifecycle Hooks**: Provides startup/shutdown coordination

### Service Types

1. **Core Services**: Essential for application operation
   - Application Controller
   - Model Manager
   - Settings Manager
   - UI Controller

2. **Feature Services**: Provide specific functionality
   - Voice System Service
   - Language Model Service
   - Context Awareness Service
   - Memory Service

3. **Utility Services**: Support the application
   - Logging Service
   - Analytics Service
   - Update Service
   - Error Handling Service

## Auto-Launch and System Integration

### macOS Integration

- **LaunchAgent Registration**: Enables automatic startup with macOS
- **Package Structure**: Follows macOS application guidelines
- **Permissions**: Manages microphone, screen recording, and accessibility permissions
- **System Tray**: Provides easy access to controls and status

### Settings Management

- **User Preferences**: Stores and applies user settings
- **Launch Options**: Controls automatic startup behavior
- **Resource Allocation**: Configure memory limits for models
- **Custom Profiles**: Different configurations for various use cases
- **Feature Toggles**: Granular control over individual components
  - Enable/disable specific models (LLM, Speech, TTS)
  - Control resource-intensive features independently
  - Set privacy preferences for different capabilities
  - Configure on-demand loading vs. preloading for each component

## Data Flow

1. **User Input** → Captured via microphone or text input
2. **Speech Recognition** → Converts audio to text using Whisper model
3. **Context Enhancement** → Adds relevant history and screen context if available
4. **Language Processing** → GPT4All processes enhanced input and decides action
5. **Action Execution** → System performs requested action (if applicable)
6. **Response Generation** → System formulates response
7. **Text-to-Speech** → Converts text response to audio via Coqui TTS
8. **User Interaction** → Presents response via UI and/or audio output

## Performance Considerations

### Memory Management

- **Dynamic Loading**: Resource-heavy components loaded only when needed
- **Quantization**: Models optimized to 4-8 bit precision
- **Memory Budget**:
  - GPT4All: ~7-9GB
  - Whisper: ~500MB
  - Tesseract OCR: ~1-2GB
  - Coqui TTS: ~1-2GB
  - FAISS: ~1GB
  - Expected Peak: ~12-14GB (of 24GB available)

### Processing Optimization

- **Parallel Execution**: Uses asyncio/multiprocessing for concurrent operations
- **Neural Engine Utilization**: Leverages Apple Silicon's Neural Engine
- **Core ML Conversion**: Performance boost for appropriate models
- **Change Detection**: Processes screenshots only when significant changes occur

### Resource Monitoring and Adjustment

- **Dynamic Resource Allocation**: Adjusts model parameters based on available resources
- **Background Processing**: Prioritizes foreground tasks, defers background work
- **Graceful Degradation**: Falls back to lighter models when resources are constrained
- **Adaptive Loading**: Pre-loads frequently used models based on usage patterns

## Security and Privacy

- **Local-First Approach**: All processing happens on the user's machine
- **No Cloud Dependency**: Functions without internet access
- **Data Storage**: Conversation history stored locally only
- **Permissions**: Explicit user approval for system operations

## Integration Points

- **macOS Integration**:
  - Accessibility API for application awareness
  - Quartz Window Services for active window capture
  - PyObjC for native macOS feature access

- **External Services** (Optional):
  - Weather APIs
  - Calendar integration
  - Email access

## Activity Log and System Monitoring

### Activity Log Design

The Activity Log panel is designed to provide complete visibility into the interactions between the user and Jarvis, as well as system events and actions taken.

#### Architecture

1. **LogEntry Component**:
   - Self-contained widget for each log entry
   - Visual differentiation by entry type
   - Timestamp and metadata storage
   - Collapsible content display

2. **Filtering System**:
   - Real-time filtering by text content
   - Type-based filtering (user, assistant, action, system)
   - Combined filter capabilities

3. **Storage and Export**:
   - In-memory storage with size limits (100 entries)
   - Export to text file for troubleshooting
   - Formatted output with timestamps and categories

4. **Signal Integration**:
   - Qt signal-based logging from all components
   - Centralized log collection
   - Event-driven updates

### System Monitor Design

The System Monitor is integrated into the Activity Log panel and provides real-time performance metrics and system information.

#### Components

1. **Performance Graphs**:
   - Real-time CPU usage visualization
   - Memory usage tracking
   - Time-series data with 60-second history
   - Auto-scaling display

2. **System Information Table**:
   - Comprehensive system details
   - Hardware information
   - Network statistics
   - Uptime and process data

3. **Resource Monitoring**:
   - Leverages psutil for cross-platform monitoring
   - Low-overhead data collection
   - Update frequency management based on visibility

4. **Integration Points**:
   - Tab-based interface with Activity Log
   - Shared styling and UI elements
   - Coordinated update cycles

### Implementation Details

The Activity Log and System Monitor are implemented using Qt's model-view architecture to efficiently manage data and presentation:

1. **Data Models**:
   - In-memory storage of log entries
   - Filtering proxy models for view customization
   - Timer-based data collection for system metrics

2. **View Components**:
   - Custom-drawn performance graphs
   - Styled table views for data presentation
   - Custom log entry widgets with type-specific formatting

3. **Optimization**:
   - Conditional updating based on visibility
   - Batched UI updates to reduce overhead
   - Efficient rendering using Qt's painting system
   - Resource usage throttling when minimized

4. **Extensibility**:
   - Plugin architecture for additional metrics
   - Custom log categories for future expansion
   - Export options for various formats

This design provides comprehensive visibility into system operation while maintaining minimal performance impact, particularly important for an assistant that needs to run continuously in the background.

## Technical Debt and Future Considerations

- **Wake Word Detection**: Need efficient always-listening capability
- **Multi-Monitor Support**: Improve screen observation across displays
- **Battery Optimization**: Add power-saving modes
- **Model Swapping**: Design for easy replacement as better models emerge
- **Installer**: Package system for easy distribution

