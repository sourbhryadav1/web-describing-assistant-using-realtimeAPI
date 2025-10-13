# 🎙️ Intelligent Voice Assistant Agent

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-Realtime%20API-412991.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**A Context-Aware Voice Assistant Powered by OpenAI's Realtime API**

*Transform any webpage into an interactive voice experience*

[Features](#-features) • [Demo](#-demo) • [Architecture](#-architecture) • [Setup](#-setup) • [Usage](#-usage) • [Documentation](#-documentation)

</div>

---

## 📖 Overview

This project is an **intelligent voice assistant agent** that can understand and interact with webpage content in real-time. It uses OpenAI's cutting-edge **Realtime API** to enable natural, low-latency voice conversations about any webpage's content.

### What Makes This Unique?

- 🧠 **Context-Aware**: Automatically analyzes webpage structure and content to provide accurate, relevant responses
- ⚡ **Real-Time Communication**: Uses WebSocket for instant, bidirectional audio streaming with minimal latency
- 🎯 **Smart Preloading**: Generates and caches page summaries before user interaction for instant responses
- 🔊 **Natural Voice**: Leverages OpenAI's advanced text-to-speech and speech-to-text models for human-like conversations
- 📱 **Cross-Platform Ready**: Backend supports both web browsers and native mobile apps (Flutter integration guides included)

> **Note:** This repository includes a **demo web interface** showcasing a fictional company ("Aura Energy") to demonstrate the voice assistant's capabilities. The core technology can be applied to any webpage or application.

---

## ✨ Features

### Core Capabilities

- **Automatic Page Summarization**
  - Extracts and analyzes webpage structure (headings, links, content)
  - Generates concise, conversational summaries using GPT-4o
  - Converts summaries to natural-sounding speech
  - Preloads summaries on page load for instant playback

- **Real-Time Voice Conversations**
  - Continuous bidirectional audio streaming
  - Context-aware responses limited to webpage content
  - Server-side voice activity detection (VAD)
  - Multi-language support (English, Hindi, and more)

- **Intelligent Content Understanding**
  - Parses HTML structure (navigation, headings, actions)
  - Extracts metadata and alt text for comprehensive context
  - Creates structured knowledge base for accurate Q&A
  - Handles follow-up questions and clarifications

- **Performance Optimizations**
  - Session preloading for near-instant startup
  - Audio buffering and queuing for smooth playback
  - Efficient WebSocket proxying
  - Memory-efficient audio processing (PCM16 format)

### Technical Features

- **Backend (FastAPI)**
  - RESTful API endpoints for session management
  - WebSocket proxy for OpenAI Realtime API
  - Asynchronous request handling
  - CORS support for cross-origin requests
  - Beautiful HTML parsing with BeautifulSoup

- **Frontend (Web Demo)**
  - Modern, responsive UI with Tailwind CSS
  - Web Audio API integration
  - Real-time audio capture and playback
  - Visual feedback (status indicators, animations)
  - Preloading strategy for optimal UX

- **Audio Processing**
  - PCM16 format at 24kHz sample rate
  - Float32 ↔ Int16 conversions
  - Base64 encoding for transmission
  - Continuous audio streaming with automatic silence detection

---

## 🎬 Demo

### Demo Website: Aura Energy

This repository includes a **demonstration webpage** featuring a fictional renewable energy company called "Aura Energy." The demo showcases:

- **Homepage** (`index.html`): Overview of solar, wind, and battery storage technologies
- **Secondary Page** (`page1.html`): Additional content to demonstrate multi-page support

**The demo is purely for illustration purposes** — the voice assistant technology can be integrated into any website or application.

### Try It Out

1. Click the **blue microphone button** (top-right corner)
2. Listen to the automated page summary
3. Ask questions about the page content
4. Examples:
   - *"What technologies does this company offer?"*
   - *"Tell me about the offshore wind turbines"*
   - *"What navigation options are available?"*

---

## 🏗️ Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     Client Layer                              │
│  ┌─────────────┐              ┌──────────────────┐          │
│  │  Web Browser │              │  Flutter App     │          │
│  │  (HTML/JS)   │              │  (Native Mobile) │          │
│  └──────┬───────┘              └────────┬─────────┘          │
└─────────┼───────────────────────────────┼────────────────────┘
          │                               │
          │    HTTP/REST + WebSocket      │
          │                               │
┌─────────▼───────────────────────────────▼────────────────────┐
│                  FastAPI Backend (Python)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Endpoints                                            │   │
│  │  • POST /summarize-and-speak                         │   │
│  │  • POST /create-talk-session                         │   │
│  │  • WebSocket /ws/realtime                            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Services                                             │   │
│  │  • HTML Parsing (BeautifulSoup)                      │   │
│  │  • Knowledge Base Generation (GPT-4o)                │   │
│  │  • Text-to-Speech (OpenAI TTS)                       │   │
│  │  • WebSocket Proxy Management                        │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            │  HTTPS + WebSocket Secure
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                  OpenAI Platform                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  • GPT-4o (Chat & Knowledge Base)                    │   │
│  │  • TTS-1 (Text-to-Speech)                            │   │
│  │  • Whisper-1 (Speech-to-Text)                        │   │
│  │  • Realtime API (Voice Conversations)                │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

#### 1. Page Load & Preloading
```
Browser → Backend: POST /summarize-and-speak
Backend → OpenAI: Page context → GPT-4o → Knowledge base
Backend → OpenAI: Summary text → TTS-1 → Audio stream
Backend → Browser: MP3 audio (preloaded)

Browser → Backend: POST /create-talk-session
Backend → OpenAI: Create ephemeral session
Backend → Browser: client_secret + model info
```

#### 2. Voice Conversation
```
User speaks → Browser captures audio (PCM16)
Browser → Backend WebSocket: Base64 encoded audio
Backend → OpenAI Realtime: Forward audio
OpenAI Realtime: Process with VAD + GPT-4o + TTS
OpenAI → Backend: Response audio (PCM16)
Backend → Browser: Forward response
Browser → Speaker: Playback audio
```

### Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend Framework** | FastAPI | Async web server & API endpoints |
| **WebSocket** | `websockets` library | Bidirectional real-time communication |
| **HTML Parsing** | BeautifulSoup4 | Extract webpage structure & content |
| **AI Models** | OpenAI GPT-4o | Knowledge base & conversation |
| **Text-to-Speech** | OpenAI TTS-1 | Natural voice synthesis |
| **Speech-to-Text** | OpenAI Whisper-1 | Audio transcription |
| **Realtime Voice** | OpenAI Realtime API | Low-latency voice conversations |
| **Audio Format** | PCM16 @ 24kHz | Standard for Realtime API |
| **Frontend** | HTML5 + Tailwind CSS | Modern, responsive UI |
| **Audio API** | Web Audio API | Browser audio capture/playback |

---

## 🚀 Setup

### Prerequisites

- **Python 3.11+** (recommended: 3.11 or 3.12)
- **OpenAI API Key** with access to:
  - GPT-4o
  - TTS-1
  - Whisper-1
  - Realtime API (preview access)
- **Modern Web Browser** (Chrome, Firefox, Edge, Safari)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/sourbhryadav1/web-describing-assistant-using-realtimeAPI.git
cd web-describing-assistant-using-realtimeAPI
```

#### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

**Important:** Never commit your `.env` file. It's already in `.gitignore`.

#### 5. Verify Installation

```bash
python -c "import fastapi, openai, websockets; print('✅ All dependencies installed')"
```

---

## 💻 Usage

### Starting the Backend Server

```bash
# Activate virtual environment first
# venv\Scripts\activate (Windows)
# source venv/bin/activate (macOS/Linux)

# Run the server
python app.py
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:5000
INFO:     Application startup complete.
```

### Accessing the Demo

1. Open your browser and navigate to: `http://127.0.0.1:5000`
2. The API root will show a welcome message
3. Open `index.html` directly in your browser:
   - **File path:** `file:///path/to/project/index.html`
   - Or use a local server (recommended):
     ```bash
     # Using Python's built-in server
     python -m http.server 8000
     ```
     Then visit: `http://localhost:8000/index.html`

### Using the Voice Assistant

#### Step 1: Preloading (Automatic)
- The page automatically preloads the summary and session on load
- Wait ~2-3 seconds for preloading to complete
- Check browser console for `[PRELOAD] ✅` messages

#### Step 2: Start Conversation
- Click the **blue microphone button** (top-right)
- The assistant will play a welcome summary
- Status indicator shows: "Loading..." → "Listening..."

#### Step 3: Interact
- Speak naturally when status shows "Listening..."
- The assistant responds in real-time
- Conversation continues until you click **Stop** (red button)

#### Step 4: End Session
- Click the button again to stop
- Status shows: "Stopping..." → "Tap to start"

### Example Questions to Ask

**General Questions:**
- "What is this page about?"
- "What can I do here?"
- "Tell me about the navigation options"

**Specific to Demo (Aura Energy):**
- "What technologies does Aura Energy offer?"
- "Explain the offshore wind turbines"
- "What is grid-scale battery storage?"
- "How do I contact the company?"

**Testing Edge Cases:**
- "What's the weather today?" → Should respond: *"I can only answer questions about this page"*
- Ask in Hindi: "यह कंपनी क्या करती है?" → Will respond in simple Hindi

---

## 📁 Project Structure

```
voice-assistant-agent/
├── app.py                          # Main FastAPI application
├── realtime.py                     # OpenAI Realtime API integration
├── tts.py                          # Text-to-speech utilities
├── stt.py                          # Speech-to-text utilities
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (create this)
├── .gitignore                      # Git ignore rules
│
├── index.html                      # Demo homepage
├── page1.html                      # Demo secondary page
│
├── README.md                       # This file
├── APP_README.md                   # Flutter integration guide
├── JSON_PARSER.md                  # JSON parsing: Web vs Flutter
├── WEB_VS_FLUTTER_COMPARISON.md    # Platform comparison guide
│
└── venv/                           # Virtual environment (gitignored)
```

### File Descriptions

| File | Description |
|------|-------------|
| `app.py` | FastAPI server with REST endpoints and WebSocket proxy |
| `realtime.py` | Handles OpenAI Realtime API session creation and management |
| `tts.py` | Text-to-speech conversion using OpenAI TTS-1 |
| `stt.py` | Speech-to-text transcription using Whisper-1 |
| `index.html` | Demo webpage with embedded voice assistant |
| `page1.html` | Secondary demo page |
| `requirements.txt` | Python package dependencies |
| `.env` | API keys and configuration (not in repo) |

---

## 🔧 Configuration

### Backend Configuration

Edit settings in `app.py`:

```python
# Server settings
HOST = "127.0.0.1"  # Change to "0.0.0.0" for mobile access
PORT = 5000

# OpenAI settings
DEFAULT_INSTRUCTIONS = "You are a friendly and helpful voice assistant..."
MODEL = "gpt-4o-realtime-preview-2024-12-17"
VOICE = "shimmer"  # Options: alloy, echo, fable, onyx, nova, shimmer

# Audio settings
AUDIO_FORMAT = "pcm16"
SAMPLE_RATE = 24000
TEMPERATURE = 0.8
MAX_TOKENS = 500
```

### Frontend Configuration

Edit settings in `index.html`:

```javascript
// Backend URL
const BACKEND_URL = 'http://127.0.0.1:5000';

// Page-specific settings
const PAGE_NAME = 'index.html';

// Preload timing
const PRELOAD_DELAY = 1000; // milliseconds
```

### Voice Assistant Behavior

Customize assistant instructions in `app.py` (WebSocket proxy section):

```python
"instructions": f"""You are a helpful voice assistant...
    Rules:
    1. Be brief but complete - keep responses under 7 seconds
    2. Only answer questions about the page content
    3. If asked about anything not on this page, say: "I can only answer questions about this page"
    4. Be conversational and helpful
    5. Always be to the point
    6. Support multiple languages naturally
"""
```

---

## 🌐 Deployment

### For Local Testing

Already covered in [Usage](#-usage) section.

### For Production

#### 1. Security Considerations

- **Never expose OpenAI API key** in client-side code
- Use **environment variables** for sensitive data
- Enable **HTTPS** for WebSocket security (WSS)
- Implement **rate limiting** to prevent abuse
- Add **authentication** for production use

#### 2. Server Deployment

**Option A: Cloud Platforms**
- **Heroku:** Add `Procfile` with `web: uvicorn app:app --host 0.0.0.0 --port $PORT`
- **AWS EC2/ECS:** Deploy with Docker container
- **Google Cloud Run:** Containerize and deploy
- **DigitalOcean App Platform:** Push to GitHub and connect

**Option B: VPS (Virtual Private Server)**
```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx

# Setup project
cd /var/www/voice-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with systemd
sudo systemctl enable voice-assistant
sudo systemctl start voice-assistant

# Configure nginx as reverse proxy
# (See nginx.conf example below)
```

**Example Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

#### 3. Environment Setup

Production `.env`:
```env
OPENAI_API_KEY=sk-prod-key-here
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://yourdomain.com
```

#### 4. Mobile Access

To access from mobile devices on the same network:

```python
# In app.py, change:
uvicorn.run(app, host="0.0.0.0", port=5000)
```

Then find your IP address:
- **Windows:** `ipconfig`
- **macOS/Linux:** `ifconfig` or `ip addr show`

Access from mobile: `http://YOUR_IP:5000`

---

## 📚 Documentation

### Additional Guides

This repository includes detailed documentation for extending and integrating the voice assistant:

| Document | Description |
|----------|-------------|
| [**APP_README.md**](APP_README.md) | Complete Flutter integration guide for building native mobile apps |
| [**JSON_PARSER.md**](JSON_PARSER.md) | Deep dive into JSON parsing differences between Web and Flutter |
| [**WEB_VS_FLUTTER_COMPARISON.md**](WEB_VS_FLUTTER_COMPARISON.md) | Side-by-side comparison of web vs native implementation |

### API Endpoints

#### `POST /summarize-and-speak`

**Description:** Generates a conversational summary of a webpage and returns audio.

**Request:**
```json
{
  "page_name": "index.html"
}
```

**Response:** Audio stream (audio/mpeg)

**Process:**
1. Parses HTML content
2. Generates knowledge base with GPT-4o
3. Creates conversational summary
4. Converts to speech with TTS-1
5. Streams audio back

---

#### `POST /create-talk-session`

**Description:** Creates an OpenAI Realtime session for voice conversations.

**Request:**
```json
{
  "page_name": "index.html"
}
```

**Response:**
```json
{
  "client_secret": "ek_abc123...",
  "model": "gpt-4o-realtime-preview-2024-12-17"
}
```

**Process:**
1. Extracts comprehensive page context
2. Creates ephemeral OpenAI session
3. Returns credentials for WebSocket connection

---

#### `WebSocket /ws/realtime`

**Description:** Bidirectional proxy for OpenAI Realtime API.

**Initial Message (Client → Server):**
```json
{
  "client_secret": "ek_abc123...",
  "model": "gpt-4o-realtime-preview-2024-12-17",
  "page_name": "index.html"
}
```

**Audio Message (Client → Server):**
```json
{
  "type": "input_audio_buffer.append",
  "audio": "base64_encoded_pcm16_audio"
}
```

**Response Messages (Server → Client):**
```json
{
  "type": "response.audio.delta",
  "delta": "base64_encoded_pcm16_audio"
}
```

**Event Types:**
- `session.created` - Session initialized
- `session.updated` - Configuration applied
- `input_audio_buffer.speech_started` - User started speaking
- `input_audio_buffer.speech_stopped` - User stopped speaking
- `response.audio.delta` - Audio chunk from assistant
- `response.audio.done` - Assistant finished speaking
- `error` - Error occurred

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Backend won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

---

#### 2. OpenAI API errors

**Error:** `401 Unauthorized` or `Invalid API key`

**Solution:**
- Verify `.env` file exists with correct API key
- Check key has no extra spaces or quotes
- Ensure key has Realtime API access (beta feature)

---

#### 3. WebSocket connection fails

**Error:** `WebSocket connection failed`

**Solution:**
- Ensure backend is running (`python app.py`)
- Check backend URL in frontend matches (default: `http://127.0.0.1:5000`)
- Verify firewall isn't blocking port 5000
- Check browser console for detailed error messages

---

#### 4. No audio playback

**Error:** Audio doesn't play in browser

**Solution:**
- Grant microphone permissions when prompted
- Check browser audio isn't muted
- Open browser DevTools → Console for errors
- Verify audio format support (PCM16 → WAV conversion)

---

#### 5. Voice detection issues

**Error:** Assistant doesn't hear me speaking

**Solution:**
- Check microphone permissions in browser settings
- Test microphone in other apps to verify it works
- Adjust silence threshold in code if needed:
  ```python
  "turn_detection": {
      "threshold": 0.3,  # Lower = more sensitive
      "silence_duration_ms": 300  # Adjust timeout
  }
  ```

---

#### 6. Slow response times

**Issue:** Long delays before assistant responds

**Solution:**
- Enable preloading (automatic in demo)
- Check internet connection speed
- Reduce `max_response_output_tokens` for shorter responses
- Use CDN for OpenAI API if available

---

#### 7. "Realtime API not available" error

**Error:** `Model 'gpt-4o-realtime' not available`

**Solution:**
- Realtime API is currently in **preview/beta**
- Request access at: https://platform.openai.com/
- Use waitlist approval email to verify access
- Check OpenAI dashboard for API access status

---

### Debug Mode

Enable detailed logging:

```python
# In app.py, add at the top:
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable:
# export LOG_LEVEL=DEBUG
```

Check logs for:
- `[INFO]` - Normal operations
- `[SUCCESS]` - Successful operations
- `[ERROR]` - Error messages with details
- `[WARN]` - Warning messages

---

## 🤝 Contributing

Contributions are welcome! This is a demo project, but improvements and bug fixes are appreciated.

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Commit with clear messages:**
   ```bash
   git commit -m "Add: amazing feature description"
   ```
5. **Push to your fork:**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**

### Contribution Ideas

- 🌍 Add support for more languages
- 📱 Create React Native integration guide
- 🎨 Improve demo UI/UX
- ⚡ Performance optimizations
- 🔒 Enhanced security features
- 📊 Analytics and usage tracking
- 🧪 Unit and integration tests
- 📝 Additional documentation
- 🐛 Bug fixes

### Code Style

- Follow **PEP 8** for Python code
- Use **meaningful variable names**
- Add **docstrings** for functions
- Keep functions **small and focused**
- Write **clear commit messages**

---

## 🧪 Testing

### Manual Testing

1. **Test Preloading:**
   - Open DevTools → Console
   - Look for `[PRELOAD] ✅` messages
   - Should complete within 3-5 seconds

2. **Test Summary Playback:**
   - Click assistant button
   - Verify audio plays immediately
   - Check status indicator updates

3. **Test Voice Conversation:**
   - Wait for "Listening..." status
   - Ask a question about page content
   - Verify assistant responds accurately
   - Try follow-up questions

4. **Test Edge Cases:**
   - Ask off-topic questions
   - Try different languages
   - Test with poor audio quality
   - Check session cleanup on stop

### Automated Testing

*Coming soon - contributions welcome!*

```bash
# Future: Run tests
pytest tests/
```

---

## 📜 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- **OpenAI** for their incredible Realtime API and AI models
- **FastAPI** for the excellent async web framework
- **Tailwind CSS** for beautiful, responsive design
- **BeautifulSoup** for reliable HTML parsing
- The **open-source community** for inspiration and tools

---

## 📞 Contact & Support

### Questions or Issues?

- **GitHub Issues:** [Create an issue](https://github.com/sourbhryadav1/web-describing-assistant-using-realtimeAPI/issues)
- **Email:** sourbhr12@gmail.com

### Resources

- [OpenAI Realtime API Documentation](https://platform.openai.com/docs/guides/realtime)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Web Audio API Guide](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [Flutter Integration Guide](./APP_README.md)

---

## 🗺️ Roadmap

### Current Version: v1.0.0-beta

### Planned Features

- [ ] **Multi-language UI** (Spanish, French, Hindi)
- [ ] **Voice customization** (choose different voices)
- [ ] **Conversation history** (save and replay sessions)
- [ ] **Advanced analytics** (usage metrics, performance tracking)
- [ ] **Mobile app templates** (React Native, Flutter)
- [ ] **Plugin system** (extend with custom integrations)
- [ ] **Admin dashboard** (monitor sessions, configure settings)
- [ ] **A/B testing framework** (optimize responses)
- [ ] **Offline mode** (cached responses for common questions)
- [ ] **Multi-user support** (authentication, personalization)

### Future Versions

- **v1.1:** Enhanced error handling and retry logic
- **v1.2:** Voice customization and language switching
- **v1.3:** Conversation history and analytics
- **v2.0:** Complete Flutter SDK with ready-to-use components

---

## 🌟 Star History

If you find this project useful, please consider giving it a ⭐ on GitHub!

```
⭐ Star this repo to show your support and help others discover it!
```

---

<div align="center">

**Built with ❤️ using OpenAI Realtime API**

[⬆ Back to Top](#-intelligent-voice-assistant-agent)

</div>

