# Flutter App Integration Guide - Voice Assistant Backend

## Overview

This guide explains how to integrate the existing FastAPI voice assistant backend with a Flutter native mobile application. The implementation provides real-time voice conversation capabilities using OpenAI's Realtime API.

---

## Backend Architecture

### Existing Backend Endpoints

Your FastAPI backend (`app.py`) provides these key endpoints:

1. **`POST /summarize-and-speak`** - Generates page summary as audio
2. **`POST /create-talk-session`** - Creates OpenAI Realtime session
3. **`WebSocket /ws/realtime`** - WebSocket proxy for real-time voice chat

### Backend URL
```
Base URL: http://127.0.0.1:5000
WebSocket: ws://127.0.0.1:5000/ws/realtime
```

---

## Flutter App Requirements

### Dependencies

Add these to your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # HTTP & WebSocket
  http: ^1.2.0
  web_socket_channel: ^2.4.0
  
  # Audio Recording & Playback
  record: ^5.0.4
  audioplayers: ^5.2.1
  permission_handler: ^11.1.0
  
  # Audio Processing (if needed for PCM conversion)
  flutter_sound: ^9.2.13
  
  # State Management
  provider: ^6.1.1  # or riverpod, bloc, etc.
  
  # JSON & Async
  async: ^2.11.0
```

---

## Flutter Implementation

### 1. Project Structure

```
lib/
├── main.dart
├── models/
│   └── realtime_message.dart
├── services/
│   ├── voice_assistant_service.dart
│   ├── audio_service.dart
│   └── websocket_service.dart
├── screens/
│   └── home_screen.dart
└── widgets/
    └── agent_button.dart
```

---

### 2. Voice Assistant Service

Create `lib/services/voice_assistant_service.dart`:

```dart
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

class VoiceAssistantService {
  static const String baseUrl = 'http://YOUR_SERVER_IP:5000';
  static const String wsUrl = 'ws://YOUR_SERVER_IP:5000/ws/realtime';
  
  WebSocketChannel? _channel;
  StreamController<Map<String, dynamic>>? _messageController;
  
  String? _clientSecret;
  String? _model;
  bool _isConnected = false;

  /// Step 1: Create Realtime Session
  Future<bool> createSession(String pageName) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/create-talk-session'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'page_name': pageName}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _clientSecret = data['client_secret'];
        _model = data['model'];
        print('[SUCCESS] Session created: $_clientSecret');
        return true;
      }
      return false;
    } catch (e) {
      print('[ERROR] Failed to create session: $e');
      return false;
    }
  }

  /// Step 2: Connect to WebSocket
  Future<bool> connectWebSocket(String pageName) async {
    if (_clientSecret == null) {
      print('[ERROR] No client secret available');
      return false;
    }

    try {
      _messageController = StreamController<Map<String, dynamic>>.broadcast();
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      
      // Send authentication message
      final authMessage = {
        'client_secret': _clientSecret,
        'model': _model,
        'page_name': pageName,
      };
      
      _channel!.sink.add(jsonEncode(authMessage));
      print('[SUCCESS] WebSocket connected and authenticated');
      
      // Listen to messages
      _channel!.stream.listen(
        (message) {
          final data = jsonDecode(message);
          _messageController?.add(data);
          _handleMessage(data);
        },
        onError: (error) {
          print('[ERROR] WebSocket error: $error');
          _isConnected = false;
        },
        onDone: () {
          print('[INFO] WebSocket closed');
          _isConnected = false;
        },
      );
      
      _isConnected = true;
      return true;
    } catch (e) {
      print('[ERROR] WebSocket connection failed: $e');
      return false;
    }
  }

  /// Handle incoming messages
  void _handleMessage(Map<String, dynamic> data) {
    switch (data['type']) {
      case 'session.created':
        print('[INFO] Session created successfully');
        break;
      case 'session.updated':
        print('[INFO] Session updated successfully');
        break;
      case 'input_audio_buffer.speech_started':
        print('[INFO] User started speaking');
        break;
      case 'input_audio_buffer.speech_stopped':
        print('[INFO] User stopped speaking');
        break;
      case 'response.audio.delta':
        // Audio chunk received - handled by audio service
        break;
      case 'response.audio.done':
        print('[INFO] Assistant finished speaking');
        break;
      case 'error':
        print('[ERROR] Realtime API error: ${data['error']}');
        break;
    }
  }

  /// Send audio chunk
  void sendAudioChunk(String base64Audio) {
    if (_isConnected && _channel != null) {
      final message = {
        'type': 'input_audio_buffer.append',
        'audio': base64Audio,
      };
      _channel!.sink.add(jsonEncode(message));
    }
  }

  /// Get message stream
  Stream<Map<String, dynamic>>? get messageStream => _messageController?.stream;

  /// Check if connected
  bool get isConnected => _isConnected;

  /// Disconnect
  void disconnect() {
    _channel?.sink.close();
    _messageController?.close();
    _isConnected = false;
    _clientSecret = null;
    _model = null;
  }
}
```

---

### 3. Audio Service

Create `lib/services/audio_service.dart`:

```dart
import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:record/record.dart';
import 'package:audioplayers/audioplayers.dart';

class AudioService {
  final AudioRecorder _recorder = AudioRecorder();
  final AudioPlayer _player = AudioPlayer();
  
  StreamController<String>? _audioStreamController;
  bool _isRecording = false;

  /// Start continuous audio recording
  Future<bool> startRecording(Function(String) onAudioChunk) async {
    try {
      // Request permission
      if (!await _recorder.hasPermission()) {
        print('[ERROR] Microphone permission denied');
        return false;
      }

      // Start recording
      final stream = await _recorder.startStream(
        RecordConfig(
          encoder: AudioEncoder.pcm16bits,
          sampleRate: 24000,
          numChannels: 1,
        ),
      );

      _isRecording = true;
      
      // Process audio stream
      stream.listen(
        (data) {
          // Convert PCM16 to base64
          final base64Audio = base64Encode(data);
          onAudioChunk(base64Audio);
        },
        onError: (error) {
          print('[ERROR] Recording error: $error');
          _isRecording = false;
        },
      );

      print('[SUCCESS] Recording started');
      return true;
    } catch (e) {
      print('[ERROR] Failed to start recording: $e');
      return false;
    }
  }

  /// Stop recording
  Future<void> stopRecording() async {
    await _recorder.stop();
    _isRecording = false;
    print('[INFO] Recording stopped');
  }

  /// Play audio chunk
  Future<void> playAudioChunk(String base64Audio) async {
    try {
      // Decode base64 to bytes
      final bytes = base64Decode(base64Audio);
      
      // Convert to WAV format (PCM16 needs WAV header)
      final wavBytes = _addWavHeader(bytes, 24000, 1, 16);
      
      // Play audio
      await _player.play(BytesSource(wavBytes));
    } catch (e) {
      print('[ERROR] Failed to play audio: $e');
    }
  }

  /// Add WAV header to PCM data
  Uint8List _addWavHeader(
    Uint8List pcmData,
    int sampleRate,
    int numChannels,
    int bitsPerSample,
  ) {
    final dataSize = pcmData.length;
    final byteRate = sampleRate * numChannels * (bitsPerSample ~/ 8);
    final blockAlign = numChannels * (bitsPerSample ~/ 8);
    
    final header = BytesBuilder();
    
    // RIFF header
    header.add(utf8.encode('RIFF'));
    header.add(_int32ToBytes(36 + dataSize)); // File size - 8
    header.add(utf8.encode('WAVE'));
    
    // fmt chunk
    header.add(utf8.encode('fmt '));
    header.add(_int32ToBytes(16)); // fmt chunk size
    header.add(_int16ToBytes(1)); // Audio format (1 = PCM)
    header.add(_int16ToBytes(numChannels));
    header.add(_int32ToBytes(sampleRate));
    header.add(_int32ToBytes(byteRate));
    header.add(_int16ToBytes(blockAlign));
    header.add(_int16ToBytes(bitsPerSample));
    
    // data chunk
    header.add(utf8.encode('data'));
    header.add(_int32ToBytes(dataSize));
    header.add(pcmData);
    
    return header.toBytes();
  }

  Uint8List _int32ToBytes(int value) {
    return Uint8List(4)
      ..[0] = value & 0xFF
      ..[1] = (value >> 8) & 0xFF
      ..[2] = (value >> 16) & 0xFF
      ..[3] = (value >> 24) & 0xFF;
  }

  Uint8List _int16ToBytes(int value) {
    return Uint8List(2)
      ..[0] = value & 0xFF
      ..[1] = (value >> 8) & 0xFF;
  }

  bool get isRecording => _isRecording;

  void dispose() {
    _recorder.dispose();
    _player.dispose();
    _audioStreamController?.close();
  }
}
```

---

### 4. Agent Button Widget

Create `lib/widgets/agent_button.dart`:

```dart
import 'package:flutter/material.dart';

class AgentButton extends StatefulWidget {
  final VoidCallback onStart;
  final VoidCallback onStop;
  final bool isActive;
  final String status;

  const AgentButton({
    Key? key,
    required this.onStart,
    required this.onStop,
    required this.isActive,
    this.status = 'Tap to start',
  }) : super(key: key);

  @override
  State<AgentButton> createState() => _AgentButtonState();
}

class _AgentButtonState extends State<AgentButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Animated button
        GestureDetector(
          onTap: widget.isActive ? widget.onStop : widget.onStart,
          child: AnimatedBuilder(
            animation: _controller,
            builder: (context, child) {
              return Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: widget.isActive ? Colors.red : Colors.blue,
                  boxShadow: widget.isActive
                      ? [
                          BoxShadow(
                            color: Colors.red.withOpacity(0.5),
                            blurRadius: 20 * _controller.value,
                            spreadRadius: 10 * _controller.value,
                          ),
                        ]
                      : [
                          BoxShadow(
                            color: Colors.blue.withOpacity(0.3),
                            blurRadius: 10,
                            spreadRadius: 2,
                          ),
                        ],
                ),
                child: Icon(
                  widget.isActive ? Icons.stop : Icons.mic,
                  color: Colors.white,
                  size: 40,
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 16),
        // Status text
        Text(
          widget.status,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}
```

---

### 5. Home Screen Implementation

Create `lib/screens/home_screen.dart`:

```dart
import 'package:flutter/material.dart';
import '../services/voice_assistant_service.dart';
import '../services/audio_service.dart';
import '../widgets/agent_button.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final VoiceAssistantService _assistantService = VoiceAssistantService();
  final AudioService _audioService = AudioService();
  
  bool _isActive = false;
  String _status = 'Tap to start';
  String _pageName = 'index.html'; // Change based on your page

  @override
  void initState() {
    super.initState();
    _setupMessageListener();
  }

  void _setupMessageListener() {
    _assistantService.messageStream?.listen((message) {
      // Handle audio playback
      if (message['type'] == 'response.audio.delta' && message['delta'] != null) {
        _audioService.playAudioChunk(message['delta']);
      }
      
      // Update status
      _updateStatus(message);
    });
  }

  void _updateStatus(Map<String, dynamic> message) {
    String newStatus = _status;
    
    switch (message['type']) {
      case 'session.updated':
        newStatus = 'Listening...';
        break;
      case 'input_audio_buffer.speech_stopped':
        newStatus = 'Processing...';
        break;
      case 'response.created':
        newStatus = 'Speaking...';
        break;
      case 'response.audio.done':
        newStatus = 'Listening...';
        break;
    }
    
    if (newStatus != _status) {
      setState(() => _status = newStatus);
    }
  }

  Future<void> _startAssistant() async {
    setState(() {
      _isActive = true;
      _status = 'Connecting...';
    });

    // Step 1: Create session
    final sessionCreated = await _assistantService.createSession(_pageName);
    if (!sessionCreated) {
      _showError('Failed to create session');
      setState(() => _isActive = false);
      return;
    }

    // Step 2: Connect WebSocket
    final wsConnected = await _assistantService.connectWebSocket(_pageName);
    if (!wsConnected) {
      _showError('Failed to connect WebSocket');
      setState(() => _isActive = false);
      return;
    }

    setState(() => _status = 'Starting audio...');

    // Step 3: Start audio recording
    final recordingStarted = await _audioService.startRecording((audioChunk) {
      _assistantService.sendAudioChunk(audioChunk);
    });

    if (!recordingStarted) {
      _showError('Failed to start recording');
      setState(() => _isActive = false);
      return;
    }

    setState(() => _status = 'Listening...');
  }

  Future<void> _stopAssistant() async {
    setState(() {
      _isActive = false;
      _status = 'Stopping...';
    });

    await _audioService.stopRecording();
    _assistantService.disconnect();

    setState(() => _status = 'Tap to start');
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  @override
  void dispose() {
    _audioService.dispose();
    _assistantService.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Voice Assistant'),
        centerTitle: true,
      ),
      body: Center(
        child: AgentButton(
          onStart: _startAssistant,
          onStop: _stopAssistant,
          isActive: _isActive,
          status: _status,
        ),
      ),
    );
  }
}
```

---

### 6. Main App Entry

Update `lib/main.dart`:

```dart
import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Voice Assistant',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
```

---

## Backend Configuration

### For Mobile Access

1. **Update Backend Host:**
   ```python
   # In app.py, change:
   uvicorn.run(app, host="0.0.0.0", port=5000)  # Not 127.0.0.1
   ```

2. **Update Flutter URLs:**
   ```dart
   // Replace with your computer's IP address
   static const String baseUrl = 'http://192.168.1.100:5000';
   static const String wsUrl = 'ws://192.168.1.100:5000/ws/realtime';
   ```

3. **Find Your IP:**
   - Windows: `ipconfig`
   - Mac/Linux: `ifconfig` or `ip addr show`

---

## Permissions Setup

### Android (`android/app/src/main/AndroidManifest.xml`)

```xml
<manifest>
    <!-- Add these permissions -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />
    
    <application>
        ...
    </application>
</manifest>
```

### iOS (`ios/Runner/Info.plist`)

```xml
<dict>
    <!-- Add these entries -->
    <key>NSMicrophoneUsageDescription</key>
    <string>This app needs microphone access for voice assistant</string>
    
    <key>NSLocalNetworkUsageDescription</key>
    <string>This app needs network access to connect to voice assistant</string>
</dict>
```

---

## Testing Steps

1. **Start Backend:**
   ```bash
   python app.py
   ```

2. **Update URLs** in Flutter code with your server IP

3. **Run Flutter App:**
   ```bash
   flutter pub get
   flutter run
   ```

4. **Test Flow:**
   - Tap agent button
   - Wait for "Listening..." status
   - Speak about page content
   - Hear AI response
   - Continue conversation

---

## Troubleshooting

### Common Issues

1. **Connection Refused:**
   - Check backend is running on `0.0.0.0:5000`
   - Verify firewall allows port 5000
   - Use correct IP address (not localhost)

2. **Audio Not Playing:**
   - Check audio permissions granted
   - Verify PCM16 format conversion
   - Test on real device (not emulator)

3. **WebSocket Timeout:**
   - Increase timeout in backend
   - Check network stability
   - Verify authentication message format

4. **Poor Audio Quality:**
   - Ensure 24kHz sample rate
   - Check PCM16 encoding
   - Add buffering if needed

---

## Advanced Features

### 1. Add Page Selection

```dart
String _selectedPage = 'index.html';

DropdownButton<String>(
  value: _selectedPage,
  items: ['index.html', 'page1.html']
      .map((page) => DropdownMenuItem(value: page, child: Text(page)))
      .toList(),
  onChanged: (value) => setState(() => _selectedPage = value!),
)
```

### 2. Add Transcript Display

```dart
List<String> _transcript = [];

// In message handler:
if (message['type'] == 'conversation.item.input_audio_transcription.completed') {
  setState(() => _transcript.add('You: ${message['transcript']}'));
}

if (message['type'] == 'response.audio_transcript.done') {
  setState(() => _transcript.add('AI: ${message['transcript']}'));
}
```

### 3. Add Error Recovery

```dart
int _retryCount = 0;
const int maxRetries = 3;

Future<void> _retryConnection() async {
  if (_retryCount < maxRetries) {
    _retryCount++;
    await Future.delayed(Duration(seconds: 2));
    await _startAssistant();
  }
}
```

---

## Production Checklist

- [ ] Use HTTPS/WSS for production
- [ ] Implement proper error handling
- [ ] Add loading indicators
- [ ] Handle background/foreground transitions
- [ ] Implement reconnection logic
- [ ] Add analytics/logging
- [ ] Test on multiple devices
- [ ] Optimize battery usage
- [ ] Add user feedback mechanisms
- [ ] Secure API endpoints

---

## Resources

- [Flutter Audio Documentation](https://pub.dev/packages/record)
- [WebSocket Channel](https://pub.dev/packages/web_socket_channel)
- [OpenAI Realtime API Docs](https://platform.openai.com/docs/guides/realtime)
- [Backend Repository](./README.md)

---

## Support

For issues or questions:
1. Check backend logs in terminal
2. Check Flutter console output
3. Verify network connectivity
4. Test with curl/Postman first

---

**Last Updated:** 2025-01-12
**Backend Version:** 1.0.0
**Compatible Flutter SDK:** >=3.0.0

