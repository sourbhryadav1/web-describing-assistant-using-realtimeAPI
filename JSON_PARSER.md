# JSON Parsing Guide - Web vs Flutter

<div align="center">

![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E.svg?logo=javascript)
![Dart](https://img.shields.io/badge/Dart-3.0+-0175C2.svg?logo=dart)
![JSON](https://img.shields.io/badge/JSON-Format-000000.svg?logo=json)

**Complete Guide to JSON Parsing Across Platforms**

*Understanding the differences between Web and Flutter JSON handling*

</div>

---

## Overview

This guide explains how **JSON parsing** works in our **web-based voice assistant demo** and how to implement equivalent (and better!) auto-parsing in **Flutter** for native mobile apps.

> **Context:** The voice assistant uses JSON for WebSocket messages, HTTP requests, and OpenAI Realtime API events. Understanding JSON parsing is crucial for implementing the Flutter version.

### What You'll Learn

- 📝 **Web JSON Parsing** - How JavaScript handles JSON automatically
- 🎯 **Flutter Approaches** - Three methods for parsing JSON in Dart
- 🔧 **Model Classes** - Type-safe JSON handling
- ⚡ **Code Generation** - Automated parsing with build tools
- ✅ **Best Practices** - Error handling and null safety

---

## 🔗 Related Documentation

- [**README.md**](./README.md) - Main project documentation
- [**APP_README.md**](./APP_README.md) - Complete Flutter integration guide
- [**WEB_VS_FLUTTER_COMPARISON.md**](./WEB_VS_FLUTTER_COMPARISON.md) - Platform comparison

---

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Web JSON Parsing](#web-json-parsing)
3. [Flutter JSON Parsing](#flutter-json-parsing)
4. [Message Models](#message-models)
5. [Code Generation](#code-generation)
6. [Complete Implementation](#complete-implementation)
7. [Best Practices](#best-practices)

---

## Overview

### What is JSON Parsing?

JSON (JavaScript Object Notation) is used for:
- WebSocket messages between client and server
- HTTP request/response bodies
- Realtime API events from OpenAI

**Example JSON:**
```json
{
  "type": "response.audio.delta",
  "delta": "SGVsbG8gd29ybGQ=",
  "event_id": "evt_123",
  "response_id": "resp_456"
}
```

---

## Web JSON Parsing

### **Automatic in JavaScript**

JavaScript has **native, dynamic** JSON parsing:

```javascript
// Parsing (JSON string → Object)
const jsonString = '{"type": "session.updated", "status": "ready"}';
const data = JSON.parse(jsonString);

// Usage - No type checking needed!
console.log(data.type);        // "session.updated"
console.log(data.status);      // "ready"
console.log(data.missing);     // undefined (no error!)

// Stringifying (Object → JSON string)
const message = {
    type: "input_audio_buffer.append",
    audio: "base64string..."
};
const jsonString = JSON.stringify(message);
```

**Advantages:**
- ✅ Extremely simple
- ✅ No setup required
- ✅ Dynamic typing

**Disadvantages:**
- ❌ No type safety
- ❌ Runtime errors if structure changes
- ❌ No autocomplete/IntelliSense
- ❌ Hard to maintain

---

### **Our Web Implementation**

```javascript
// Receiving WebSocket message
realtimeWebSocket.onmessage = (event) => {
    const data = JSON.parse(event.data);  // ← Automatic parsing
    handleRealtimeMessage(data);
};

function handleRealtimeMessage(data) {
    // Access properties directly
    switch (data.type) {
        case 'response.audio.delta':
            if (data.delta) {  // ← No type checking
                playAudioChunk(data.delta);
            }
            break;
        case 'response.audio_transcript.done':
            console.log("AI:", data.transcript);  // ← Direct access
            break;
    }
}

// Sending WebSocket message
const message = {
    type: "input_audio_buffer.append",
    audio: base64Audio
};
realtimeWebSocket.send(JSON.stringify(message));  // ← Automatic stringify
```

**No models, no classes, no setup - just works!**

---

## Flutter JSON Parsing

### **Three Approaches**

Flutter requires **manual** JSON parsing since Dart is statically typed:

1. **Manual Parsing** (Simple, verbose)
2. **Model Classes** (Recommended, type-safe)
3. **Code Generation** (Best for complex apps)

---

### **Approach 1: Manual Parsing (Quick & Dirty)**

```dart
// Receiving WebSocket message
_channel.stream.listen((message) {
  final data = jsonDecode(message) as Map<String, dynamic>;
  _handleRealtimeMessage(data);
});

void _handleRealtimeMessage(Map<String, dynamic> data) {
  // Manual type casting required
  final type = data['type'] as String?;
  
  switch (type) {
    case 'response.audio.delta':
      final delta = data['delta'] as String?;
      if (delta != null) {
        playAudioChunk(delta);
      }
      break;
    case 'response.audio_transcript.done':
      final transcript = data['transcript'] as String?;
      print('AI: $transcript');
      break;
  }
}

// Sending WebSocket message
final message = {
  'type': 'input_audio_buffer.append',
  'audio': base64Audio,
};
_channel.sink.add(jsonEncode(message));
```

**Pros:**
- ✅ Simple, no setup
- ✅ Works for simple cases

**Cons:**
- ❌ Lots of type casting (`as String?`)
- ❌ Easy to make mistakes
- ❌ No autocomplete
- ❌ Null safety issues

---

### **Approach 2: Model Classes (Recommended)**

Create model classes for each message type:

```dart
// lib/models/realtime_message.dart

/// Base class for all Realtime API messages
abstract class RealtimeMessage {
  final String type;
  final String? eventId;

  RealtimeMessage({
    required this.type,
    this.eventId,
  });

  factory RealtimeMessage.fromJson(Map<String, dynamic> json) {
    final type = json['type'] as String;
    
    switch (type) {
      case 'session.created':
        return SessionCreatedMessage.fromJson(json);
      case 'session.updated':
        return SessionUpdatedMessage.fromJson(json);
      case 'response.audio.delta':
        return ResponseAudioDeltaMessage.fromJson(json);
      case 'response.audio_transcript.done':
        return ResponseAudioTranscriptDoneMessage.fromJson(json);
      case 'input_audio_buffer.speech_started':
        return InputAudioSpeechStartedMessage.fromJson(json);
      case 'input_audio_buffer.speech_stopped':
        return InputAudioSpeechStoppedMessage.fromJson(json);
      case 'error':
        return ErrorMessage.fromJson(json);
      default:
        return UnknownMessage.fromJson(json);
    }
  }

  Map<String, dynamic> toJson();
}

/// Session Created Message
class SessionCreatedMessage extends RealtimeMessage {
  final String sessionId;
  final String model;

  SessionCreatedMessage({
    required String type,
    required this.sessionId,
    required this.model,
    String? eventId,
  }) : super(type: type, eventId: eventId);

  factory SessionCreatedMessage.fromJson(Map<String, dynamic> json) {
    return SessionCreatedMessage(
      type: json['type'] as String,
      sessionId: json['session']?['id'] as String? ?? '',
      model: json['session']?['model'] as String? ?? '',
      eventId: json['event_id'] as String?,
    );
  }

  @override
  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'session': {
        'id': sessionId,
        'model': model,
      },
      if (eventId != null) 'event_id': eventId,
    };
  }
}

/// Session Updated Message
class SessionUpdatedMessage extends RealtimeMessage {
  SessionUpdatedMessage({
    required String type,
    String? eventId,
  }) : super(type: type, eventId: eventId);

  factory SessionUpdatedMessage.fromJson(Map<String, dynamic> json) {
    return SessionUpdatedMessage(
      type: json['type'] as String,
      eventId: json['event_id'] as String?,
    );
  }

  @override
  Map<String, dynamic> toJson() {
    return {
      'type': type,
      if (eventId != null) 'event_id': eventId,
    };
  }
}

/// Response Audio Delta (contains audio chunk)
class ResponseAudioDeltaMessage extends RealtimeMessage {
  final String delta;  // Base64 encoded audio
  final int? contentIndex;
  final int? audioStartMs;
  final int? audioEndMs;

  ResponseAudioDeltaMessage({
    required String type,
    required this.delta,
    this.contentIndex,
    this.audioStartMs,
    this.audioEndMs,
    String? eventId,
  }) : super(type: type, eventId: eventId);

  factory ResponseAudioDeltaMessage.fromJson(Map<String, dynamic> json) {
    return ResponseAudioDeltaMessage(
      type: json['type'] as String,
      delta: json['delta'] as String,
      contentIndex: json['content_index'] as int?,
      audioStartMs: json['audio_start_ms'] as int?,
      audioEndMs: json['audio_end_ms'] as int?,
      eventId: json['event_id'] as String?,
    );
  }

  @override
  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'delta': delta,
      if (contentIndex != null) 'content_index': contentIndex,
      if (audioStartMs != null) 'audio_start_ms': audioStartMs,
      if (audioEndMs != null) 'audio_end_ms': audioEndMs,
      if (eventId != null) 'event_id': eventId,
    };
  }
}

/// Response Audio Transcript Done
class ResponseAudioTranscriptDoneMessage extends RealtimeMessage {
  final String transcript;
  final int? contentIndex;

  ResponseAudioTranscriptDoneMessage({
    required String type,
    required this.transcript,
    this.contentIndex,
    String? eventId,
  }) : super(type: type, eventId: eventId);

  factory ResponseAudioTranscriptDoneMessage.fromJson(Map<String, dynamic> json) {
    return ResponseAudioTranscriptDoneMessage(
      type: json['type'] as String,
      transcript: json['transcript'] as String? ?? '',
      contentIndex: json['content_index'] as int?,
      eventId: json['event_id'] as String?,
    );
  }

  @override
  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'transcript': transcript,
      if (contentIndex != null) 'content_index': contentIndex,
      if (eventId != null) 'event_id': eventId,
    };
  }
}

/// Input Audio Speech Started
class InputAudioSpeechStartedMessage extends RealtimeMessage {
  final int audioStartMs;
  final int itemId;

  InputAudioSpeechStartedMessage({
    required String type,
    required this.audioStartMs,
    required this.itemId,
    String? eventId,
  }) : super(type: type, eventId: eventId);

  factory InputAudioSpeechStartedMessage.fromJson(Map<String, dynamic> json) {
    return InputAudioSpeechStartedMessage(
      type: json['type'] as String,
      audioStartMs: json['audio_start_ms'] as int? ?? 0,
      itemId: json['item_id'] as int? ?? 0,
      eventId: json['event_id'] as String?,
    );
  }

  @override
  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'audio_start_ms': audioStartMs,
      'item_id': itemId,
      if (eventId != null) 'event_id': eventId,
    };
  }
}

/// Input Audio Speech Stopped
class InputAudioSpeechStoppedMessage extends RealtimeMessage {
  final int audioEndMs;
  final int itemId;

  InputAudioSpeechStoppedMessage({
    required String type,
    required this.audioEndMs,
    required this.itemId,
    String? eventId,
  }) : super(type: type, eventId: eventId);

  factory InputAudioSpeechStoppedMessage.fromJson(Map<String, dynamic> json) {
    return InputAudioSpeechStoppedMessage(
      type: json['type'] as String,
      audioEndMs: json['audio_end_ms'] as int? ?? 0,
      itemId: json['item_id'] as int? ?? 0,
      eventId: json['event_id'] as String?,
    );
  }

  @override
  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'audio_end_ms': audioEndMs,
      'item_id': itemId,
      if (eventId != null) 'event_id': eventId,
    };
  }
}

/// Error Message
class ErrorMessage extends RealtimeMessage {
  final Map<String, dynamic> error;
  final String? code;
  final String? message;

  ErrorMessage({
    required String type,
    required this.error,
    this.code,
    this.message,
    String? eventId,
  }) : super(type: type, eventId: eventId);

  factory ErrorMessage.fromJson(Map<String, dynamic> json) {
    final errorData = json['error'] as Map<String, dynamic>? ?? {};
    return ErrorMessage(
      type: json['type'] as String,
      error: errorData,
      code: errorData['code'] as String?,
      message: errorData['message'] as String?,
      eventId: json['event_id'] as String?,
    );
  }

  @override
  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'error': error,
      if (eventId != null) 'event_id': eventId,
    };
  }
}

/// Unknown Message (for messages we don't explicitly handle)
class UnknownMessage extends RealtimeMessage {
  final Map<String, dynamic> rawData;

  UnknownMessage({
    required String type,
    required this.rawData,
    String? eventId,
  }) : super(type: type, eventId: eventId);

  factory UnknownMessage.fromJson(Map<String, dynamic> json) {
    return UnknownMessage(
      type: json['type'] as String,
      rawData: json,
      eventId: json['event_id'] as String?,
    );
  }

  @override
  Map<String, dynamic> toJson() => rawData;
}
```

---

## Usage in Services

### **Web (JavaScript)**

```javascript
// Receiving
realtimeWebSocket.onmessage = (event) => {
    const data = JSON.parse(event.data);  // ← One line!
    
    // Direct access - no type checking
    if (data.type === 'response.audio.delta') {
        playAudio(data.delta);
    }
};

// Sending
const message = {
    type: "input_audio_buffer.append",
    audio: base64String
};
realtimeWebSocket.send(JSON.stringify(message));  // ← One line!
```

---

### **Flutter (Dart) - Using Models**

```dart
// lib/services/websocket_service.dart
import '../models/realtime_message.dart';
import 'dart:convert';

class WebSocketService {
  // Receiving
  void _listenToMessages() {
    _channel.stream.listen((rawMessage) {
      // Parse JSON string to Map
      final jsonData = jsonDecode(rawMessage) as Map<String, dynamic>;
      
      // Convert to typed model
      final message = RealtimeMessage.fromJson(jsonData);
      
      // Type-safe handling
      if (message is ResponseAudioDeltaMessage) {
        _audioService.playChunk(message.delta);  // ← Autocomplete works!
      } else if (message is SessionUpdatedMessage) {
        _startAudioCapture();
      } else if (message is ResponseAudioTranscriptDoneMessage) {
        print('AI: ${message.transcript}');  // ← Type-safe!
      }
    });
  }

  // Sending
  void sendAudioChunk(String base64Audio) {
    final message = InputAudioAppendMessage(
      type: 'input_audio_buffer.append',
      audio: base64Audio,
    );
    
    // Convert model to JSON
    final jsonString = jsonEncode(message.toJson());
    _channel.sink.add(jsonString);
  }
}
```

**Advantages:**
- ✅ Type-safe (compile-time errors)
- ✅ Autocomplete/IntelliSense
- ✅ Easy to maintain
- ✅ Self-documenting code

---

## Complete Model Implementation

### **Input Messages (Client → Server)**

```dart
// lib/models/input_messages.dart

/// Send audio chunk to server
class InputAudioAppendMessage {
  final String type;
  final String audio;  // Base64 encoded PCM16

  InputAudioAppendMessage({
    this.type = 'input_audio_buffer.append',
    required this.audio,
  });

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'audio': audio,
    };
  }
}

/// Commit audio buffer (tell server to process)
class InputAudioCommitMessage {
  final String type;

  InputAudioCommitMessage({
    this.type = 'input_audio_buffer.commit',
  });

  Map<String, dynamic> toJson() {
    return {
      'type': type,
    };
  }
}

/// Session update configuration
class SessionUpdateMessage {
  final String type;
  final SessionConfig session;

  SessionUpdateMessage({
    this.type = 'session.update',
    required this.session,
  });

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'session': session.toJson(),
    };
  }
}

class SessionConfig {
  final List<String> modalities;
  final String instructions;
  final String voice;
  final String inputAudioFormat;
  final String outputAudioFormat;
  final TurnDetectionConfig? turnDetection;
  final double temperature;
  final int maxResponseOutputTokens;

  SessionConfig({
    this.modalities = const ['text', 'audio'],
    required this.instructions,
    this.voice = 'shimmer',
    this.inputAudioFormat = 'pcm16',
    this.outputAudioFormat = 'pcm16',
    this.turnDetection,
    this.temperature = 0.8,
    this.maxResponseOutputTokens = 500,
  });

  Map<String, dynamic> toJson() {
    return {
      'modalities': modalities,
      'instructions': instructions,
      'voice': voice,
      'input_audio_format': inputAudioFormat,
      'output_audio_format': outputAudioFormat,
      if (turnDetection != null) 'turn_detection': turnDetection!.toJson(),
      'temperature': temperature,
      'max_response_output_tokens': maxResponseOutputTokens,
    };
  }
}

class TurnDetectionConfig {
  final String type;
  final double threshold;
  final int prefixPaddingMs;
  final int silenceDurationMs;

  TurnDetectionConfig({
    this.type = 'server_vad',
    this.threshold = 0.5,
    this.prefixPaddingMs = 300,
    this.silenceDurationMs = 200,
  });

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'threshold': threshold,
      'prefix_padding_ms': prefixPaddingMs,
      'silence_duration_ms': silenceDurationMs,
    };
  }
}
```

---

### **Output Messages (Server → Client)**

Already covered above in the `RealtimeMessage` class hierarchy.

---

## Code Generation (Advanced)

For large applications, use **automatic code generation**:

### **Setup**

Add to `pubspec.yaml`:
```yaml
dependencies:
  json_annotation: ^4.8.1

dev_dependencies:
  build_runner: ^2.4.6
  json_serializable: ^6.7.1
```

### **Annotated Model**

```dart
// lib/models/realtime_message.g.dart
import 'package:json_annotation/json_annotation.dart';

part 'realtime_message.g.dart';  // Generated file

@JsonSerializable()
class ResponseAudioDeltaMessage {
  final String type;
  final String delta;
  
  @JsonKey(name: 'event_id')
  final String? eventId;
  
  @JsonKey(name: 'content_index')
  final int? contentIndex;

  ResponseAudioDeltaMessage({
    required this.type,
    required this.delta,
    this.eventId,
    this.contentIndex,
  });

  // Code generation creates these automatically
  factory ResponseAudioDeltaMessage.fromJson(Map<String, dynamic> json) =>
      _$ResponseAudioDeltaMessageFromJson(json);
  
  Map<String, dynamic> toJson() =>
      _$ResponseAudioDeltaMessageToJson(this);
}
```

### **Generate Code**

Run in terminal:
```bash
flutter pub run build_runner build
```

This generates `.g.dart` files with all parsing code automatically!

**Pros:**
- ✅ Zero boilerplate
- ✅ Type-safe
- ✅ Handles complex nested objects
- ✅ Supports custom serialization

**Cons:**
- ❌ Build step required
- ❌ Learning curve
- ❌ Generated code can be hard to debug

---

## Practical Implementation

### **Recommended Structure**

```dart
// lib/models/
├── realtime_message.dart        // Base class + factory
├── input_messages.dart          // Client → Server
├── output_messages.dart         // Server → Client
└── session_config.dart          // Configuration objects

// lib/services/
├── websocket_service.dart       // Uses models for parsing
├── audio_service.dart           // Type-safe audio handling
└── voice_assistant_service.dart // Orchestrates everything
```

---

## Complete Service Example

```dart
// lib/services/websocket_service.dart
import 'package:web_socket_channel/web_socket_channel.dart';
import '../models/realtime_message.dart';
import '../models/input_messages.dart';
import 'dart:convert';
import 'dart:async';

class WebSocketService {
  WebSocketChannel? _channel;
  final StreamController<RealtimeMessage> _messageController = 
      StreamController.broadcast();
  
  // Type-safe message stream
  Stream<RealtimeMessage> get messageStream => _messageController.stream;

  Future<void> connect({
    required String clientSecret,
    required String model,
    required String pageName,
  }) async {
    final wsUrl = 'ws://YOUR_IP:5000/ws/realtime';
    _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
    
    // Send auth message
    final authMessage = {
      'client_secret': clientSecret,
      'model': model,
      'page_name': pageName,
    };
    _channel!.sink.add(jsonEncode(authMessage));
    
    // Listen to messages
    _channel!.stream.listen(
      (rawMessage) {
        try {
          // Parse JSON
          final jsonData = jsonDecode(rawMessage) as Map<String, dynamic>;
          
          // Convert to typed model
          final message = RealtimeMessage.fromJson(jsonData);
          
          // Broadcast typed message
          _messageController.add(message);
          
        } catch (e) {
          print('[ERROR] Failed to parse message: $e');
        }
      },
      onError: (error) {
        print('[ERROR] WebSocket error: $error');
      },
    );
  }

  /// Send audio chunk (type-safe)
  void sendAudioChunk(String base64Audio) {
    final message = InputAudioAppendMessage(audio: base64Audio);
    _channel?.sink.add(jsonEncode(message.toJson()));
  }

  /// Send session update (type-safe)
  void updateSession(SessionConfig config) {
    final message = SessionUpdateMessage(session: config);
    _channel?.sink.add(jsonEncode(message.toJson()));
  }

  void disconnect() {
    _channel?.sink.close();
    _messageController.close();
  }
}
```

---

## Usage in UI Layer

### **Web (JavaScript)**

```javascript
// Direct property access
realtimeWebSocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'response.audio.delta') {
        playAudio(data.delta);  // Hope delta exists!
    }
};
```

---

### **Flutter (Dart) - Type-Safe**

```dart
// lib/screens/home_screen.dart

@override
void initState() {
  super.initState();
  
  // Listen to typed messages
  _wsService.messageStream.listen((message) {
    if (message is ResponseAudioDeltaMessage) {
      // Autocomplete knows 'delta' exists!
      _audioService.playChunk(message.delta);
      
    } else if (message is SessionUpdatedMessage) {
      _startAudioCapture();
      
    } else if (message is ResponseAudioTranscriptDoneMessage) {
      // Autocomplete knows 'transcript' exists!
      print('🗣️ AI: ${message.transcript}');
      setState(() => _aiText = message.transcript);
      
    } else if (message is InputAudioSpeechStartedMessage) {
      setState(() => _status = 'Listening...');
      
    } else if (message is InputAudioSpeechStoppedMessage) {
      setState(() => _status = 'Processing...');
      
    } else if (message is ErrorMessage) {
      print('❌ Error: ${message.message}');
      _showError(message.message ?? 'Unknown error');
    }
  });
}
```

**Benefits:**
- ✅ IDE autocomplete for all properties
- ✅ Compile-time error if property doesn't exist
- ✅ Easy refactoring (rename works everywhere)
- ✅ Self-documenting (models show structure)

---

## Comparison Table

| Aspect | Web (JavaScript) | Flutter (Manual) | Flutter (Models) | Flutter (Generated) |
|--------|------------------|------------------|------------------|---------------------|
| **Setup** | None | None | Create models | Add packages + generate |
| **Code** | `JSON.parse()` | `jsonDecode()` + casting | Model classes | Annotations |
| **Type Safety** | ❌ None | ⚠️ Partial | ✅ Full | ✅ Full |
| **Autocomplete** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Null Safety** | ❌ No | ⚠️ Manual | ✅ Built-in | ✅ Built-in |
| **Errors** | Runtime | Runtime | Compile-time | Compile-time |
| **Refactoring** | ❌ Hard | ❌ Hard | ✅ Easy | ✅ Easy |
| **Performance** | Fast | Fast | Fast | Fast |
| **Maintenance** | ❌ Hard | ❌ Hard | ✅ Easy | ✅ Easiest |

---

## Real-World Example

### **Scenario: Handle Audio Response**

#### **Web**
```javascript
realtimeWebSocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // No safety - hope these exist!
    if (data.type === 'response.audio.delta') {
        playAudio(data.delta);
    }
    
    if (data.type === 'response.audio_transcript.done') {
        console.log(data.transcript);
    }
};
```

#### **Flutter (Manual)**
```dart
_channel.stream.listen((message) {
  final data = jsonDecode(message) as Map<String, dynamic>;
  final type = data['type'] as String?;
  
  if (type == 'response.audio.delta') {
    final delta = data['delta'] as String?;  // Manual cast
    if (delta != null) {
      playAudio(delta);
    }
  }
  
  if (type == 'response.audio_transcript.done') {
    final transcript = data['transcript'] as String?;
    print(transcript);
  }
});
```

#### **Flutter (With Models)**
```dart
_wsService.messageStream.listen((message) {
  // Pattern matching with type safety!
  switch (message) {
    case ResponseAudioDeltaMessage():
      playAudio(message.delta);  // ← IDE knows delta exists!
      break;
      
    case ResponseAudioTranscriptDoneMessage():
      print(message.transcript);  // ← Type-safe, autocomplete works!
      break;
      
    case ErrorMessage():
      showError(message.message);
      break;
  }
});
```

---

## Best Practices

### **1. Always Validate JSON**

```dart
// Bad
final data = jsonDecode(message);
playAudio(data['delta']);  // 💥 Crashes if delta is missing

// Good
final data = jsonDecode(message) as Map<String, dynamic>;
final delta = data['delta'] as String?;
if (delta != null) {
  playAudio(delta);
}

// Better
final message = RealtimeMessage.fromJson(data);
if (message is ResponseAudioDeltaMessage) {
  playAudio(message.delta);  // Can't be null, guaranteed by model
}
```

---

### **2. Handle Unknown Messages**

```dart
factory RealtimeMessage.fromJson(Map<String, dynamic> json) {
  final type = json['type'] as String;
  
  switch (type) {
    case 'response.audio.delta':
      return ResponseAudioDeltaMessage.fromJson(json);
    // ... other cases ...
    default:
      // Don't crash on unknown messages!
      return UnknownMessage.fromJson(json);
  }
}
```

---

### **3. Use Null Safety**

```dart
class ResponseMessage {
  final String type;
  final String? transcript;  // ← Nullable
  final String delta;        // ← Non-nullable

  ResponseMessage({
    required this.type,
    this.transcript,           // Optional
    required this.delta,       // Required
  });

  factory ResponseMessage.fromJson(Map<String, dynamic> json) {
    return ResponseMessage(
      type: json['type'] as String,
      transcript: json['transcript'] as String?,  // ← Can be null
      delta: json['delta'] as String? ?? '',      // ← Default value
    );
  }
}
```

---

### **4. Extension Methods for Convenience**

```dart
// lib/extensions/json_extensions.dart

extension MapExtensions on Map<String, dynamic> {
  /// Safely get string value
  String? getString(String key) {
    return this[key] as String?;
  }

  /// Safely get int value
  int? getInt(String key) {
    return this[key] as int?;
  }

  /// Get string with default
  String getStringOrDefault(String key, String defaultValue) {
    return getString(key) ?? defaultValue;
  }
}

// Usage
final data = jsonDecode(message) as Map<String, dynamic>;
final type = data.getString('type');
final delta = data.getString('delta');
```

---

## Testing

### **Unit Tests for Models**

```dart
// test/models/realtime_message_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:your_app/models/realtime_message.dart';

void main() {
  group('ResponseAudioDeltaMessage', () {
    test('should parse valid JSON', () {
      final json = {
        'type': 'response.audio.delta',
        'delta': 'SGVsbG8=',
        'event_id': 'evt_123',
      };

      final message = ResponseAudioDeltaMessage.fromJson(json);

      expect(message.type, 'response.audio.delta');
      expect(message.delta, 'SGVsbG8=');
      expect(message.eventId, 'evt_123');
    });

    test('should handle missing optional fields', () {
      final json = {
        'type': 'response.audio.delta',
        'delta': 'SGVsbG8=',
      };

      final message = ResponseAudioDeltaMessage.fromJson(json);

      expect(message.eventId, isNull);
      expect(message.contentIndex, isNull);
    });

    test('should serialize to JSON', () {
      final message = ResponseAudioDeltaMessage(
        type: 'response.audio.delta',
        delta: 'SGVsbG8=',
      );

      final json = message.toJson();

      expect(json['type'], 'response.audio.delta');
      expect(json['delta'], 'SGVsbG8=');
    });
  });
}
```

---

## Performance Considerations

### **JSON Parsing Performance**

```dart
// ❌ Slow - Parse every time
_channel.stream.listen((message) {
  final data1 = jsonDecode(message);  // Parse
  final type = data1['type'];
  
  final data2 = jsonDecode(message);  // Parse again!
  final delta = data2['delta'];
});

// ✅ Fast - Parse once
_channel.stream.listen((message) {
  final data = jsonDecode(message);  // Parse once
  final type = data['type'];
  final delta = data['delta'];
});

// ✅ Fastest - Parse once + type-safe
_channel.stream.listen((message) {
  final data = jsonDecode(message);
  final msg = RealtimeMessage.fromJson(data);  // Type-safe wrapper
  
  if (msg is ResponseAudioDeltaMessage) {
    playAudio(msg.delta);  // Direct access
  }
});
```

---

## Migration Guide: Web → Flutter

### **Step 1: Identify All JSON Structures**

In your web app, find all places where you parse JSON:

```javascript
// Web - Find these patterns
JSON.parse(...)
JSON.stringify(...)
data.property
message.field
```

### **Step 2: Create Model Classes**

For each unique JSON structure, create a Dart model:

```dart
// Example: Session info response
// Web JSON:
// {
//   "client_secret": "ek_abc123",
//   "model": "gpt-4o-realtime-preview-2024-12-17"
// }

// Flutter Model:
class SessionInfo {
  final String clientSecret;
  final String model;

  SessionInfo({
    required this.clientSecret,
    required this.model,
  });

  factory SessionInfo.fromJson(Map<String, dynamic> json) {
    return SessionInfo(
      clientSecret: json['client_secret'] as String,
      model: json['model'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'client_secret': clientSecret,
      'model': model,
    };
  }
}
```

### **Step 3: Replace JSON.parse/stringify**

```dart
// Web
const data = JSON.parse(jsonString);
const output = JSON.stringify(object);

// Flutter
final data = jsonDecode(jsonString) as Map<String, dynamic>;
final output = jsonEncode(object);
```

### **Step 4: Add Type Safety**

```dart
// Web (no safety)
if (data.type === 'audio') {
    play(data.delta);  // Hope it exists!
}

// Flutter (type-safe)
final message = RealtimeMessage.fromJson(data);
if (message is ResponseAudioDeltaMessage) {
    play(message.delta);  // Guaranteed to exist!
}
```

---

## Summary

### **Web Approach: Simple but Unsafe**
```javascript
✅ One-line parsing: JSON.parse()
✅ Direct property access: data.property
❌ No type safety
❌ Runtime errors
❌ No autocomplete
```

### **Flutter Approach: More Code, Much Safer**
```dart
✅ Type-safe models
✅ Compile-time errors
✅ Full autocomplete
✅ Easy to maintain
⚠️ Requires model classes
⚠️ More initial setup
```

### **Recommendation**

For the voice assistant Flutter app:

1. **Start with Manual Parsing** (if prototyping quickly)
2. **Move to Model Classes** (recommended for production)
3. **Consider Code Generation** (if app grows large)

The model class approach gives you the best balance of:
- Type safety
- Maintainability
- Performance
- Development experience

---

## Quick Reference

### **Common Operations**

| Operation | Web | Flutter |
|-----------|-----|---------|
| Parse JSON string | `JSON.parse(str)` | `jsonDecode(str)` |
| Create JSON string | `JSON.stringify(obj)` | `jsonEncode(obj)` |
| Access property | `data.property` | `data['property']` |
| Type-safe access | N/A | `model.property` |
| Check property exists | `data.property !== undefined` | `data['property'] != null` |
| Nested access | `data.user.name` | `data['user']?['name']` |
| Array access | `data.items[0]` | `data['items']?[0]` |

---

## 📊 Quick Reference Table

| Feature | Web (JavaScript) | Flutter (Dart) |
|---------|------------------|----------------|
| **Parsing** | `JSON.parse(str)` | `jsonDecode(str)` |
| **Stringify** | `JSON.stringify(obj)` | `jsonEncode(obj)` |
| **Type Safety** | ❌ None | ✅ Full (with models) |
| **Autocomplete** | ❌ No | ✅ Yes (with models) |
| **Setup** | None | Model classes |
| **Errors** | Runtime | Compile-time (with models) |
| **Best For** | Quick prototypes | Production apps |

---

## 💡 Key Takeaway

**JavaScript** makes JSON parsing trivially easy but unsafe. **Dart** requires more setup with model classes, but provides:
- ✅ Type safety
- ✅ Autocomplete
- ✅ Compile-time error checking
- ✅ Better maintainability

**For the voice assistant Flutter app, we recommend using model classes (Approach 2) for the best balance of safety and simplicity.**

---

**Last Updated:** January 2025  
**For:** Voice Assistant Flutter Migration  
**Project:** [Voice Assistant Agent Demo](./README.md)

---

<div align="center">

**Part of the Voice Assistant Agent Demo Project**

[⬆ Back to Top](#json-parsing-guide---web-vs-flutter) • [Main README](./README.md) • [Flutter Guide](./APP_README.md)

</div>


