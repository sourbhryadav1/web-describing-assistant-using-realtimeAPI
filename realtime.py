import os
import json
import asyncio
import websockets
from openai import AsyncOpenAI
from dotenv import load_dotenv
import base64
import aiohttp

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Initialize OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

class RealtimeVoiceAssistant:
    def __init__(self):
        self.client_secret = None
        self.websocket = None
        self.session_id = None
        self.is_connected = False
        
    async def create_session(self, page_context: str, page_title: str):
        """
        Creates a new OpenAI Realtime session with page-specific context
        """
        try:
            # Create the session using direct HTTP request
            url = "https://api.openai.com/v1/realtime/sessions"
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-realtime-preview-2024-12-17",
                "voice": "shimmer",
                "instructions": f"""
                You are a helpful voice assistant for the webpage '{page_title}'. 
                Your knowledge is strictly limited to the information provided below.
                
                PAGE CONTEXT:
                {page_context}
                
                Rules:
                1. Be extremely brief - responses should be under 10 seconds (25-30 words max)
                2. Only answer questions about the page content above
                3. If asked about anything not on this page, say: "I can only answer questions about the content on this page. You could ask me about our core technologies, for example."
                4. Be conversational and helpful
                """,
                "temperature": 0.8,
                "max_response_output_tokens": 100
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[ERROR] Failed to create session: {response.status} - {error_text}")
                        return None
                    
                    session_data = await response.json()
                    
                    self.client_secret = session_data["client_secret"]["value"]
                    self.session_id = session_data["id"]
                    self.model = session_data.get("model", "gpt-realtime")
                    
                    print(f"[SUCCESS] Created Realtime session: {self.session_id} with model: {self.model}")
                    return {
                        "client_secret": self.client_secret,
                        "model": self.model
                    }
            
        except Exception as e:
            print(f"[ERROR] Failed to create Realtime session: {e}")
            return None
    
    async def connect_to_session(self, client_secret: str):
        """
        Connects to the Realtime session via WebSocket
        """
        try:
            # Connect to the Realtime API WebSocket
            ws_url = f"wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01&client_secret={client_secret}"
            
            self.websocket = await websockets.connect(ws_url)
            self.is_connected = True
            
            print("[SUCCESS] Connected to Realtime WebSocket")
            
            # Start listening for messages
            await self.listen_for_messages()
            
        except Exception as e:
            print(f"[ERROR] Failed to connect to Realtime session: {e}")
            self.is_connected = False
            return False
    
    async def listen_for_messages(self):
        """
        Listens for incoming messages from the Realtime API
        """
        try:
            async for message in self.websocket:
                data = json.loads(message)
                
                if data.get("type") == "conversation.item.input_audio_buffer.speech_started":
                    print("[INFO] User started speaking")
                    
                elif data.get("type") == "conversation.item.input_audio_buffer.speech_stopped":
                    print("[INFO] User stopped speaking")
                    
                elif data.get("type") == "conversation.item.output_audio_buffer.speech_started":
                    print("[INFO] Assistant started speaking")
                    
                elif data.get("type") == "conversation.item.output_audio_buffer.speech_stopped":
                    print("[INFO] Assistant finished speaking")
                    
                elif data.get("type") == "error":
                    print(f"[ERROR] Realtime API error: {data.get('error')}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("[INFO] WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            print(f"[ERROR] Error listening for messages: {e}")
            self.is_connected = False
    
    async def send_audio(self, audio_data: bytes):
        """
        Sends audio data to the Realtime API
        """
        if not self.is_connected or not self.websocket:
            print("[ERROR] Not connected to Realtime session")
            return False
            
        try:
            # Encode audio as base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Send audio data
            message = {
                "type": "conversation.item.input_audio_buffer.append",
                "item": {
                    "type": "input_audio_buffer",
                    "audio": audio_base64
                }
            }
            
            await self.websocket.send(json.dumps(message))
            print("[SUCCESS] Audio sent to Realtime API")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to send audio: {e}")
            return False
    
    async def commit_audio(self):
        """
        Commits the audio buffer to trigger processing
        """
        if not self.is_connected or not self.websocket:
            return False
            
        try:
            message = {
                "type": "conversation.item.input_audio_buffer.commit"
            }
            
            await self.websocket.send(json.dumps(message))
            print("[SUCCESS] Audio buffer committed")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to commit audio: {e}")
            return False
    
    async def disconnect(self):
        """
        Disconnects from the Realtime session
        """
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            print("[INFO] Disconnected from Realtime session")
    
    async def cleanup_session(self):
        """
        Cleans up the Realtime session
        """
        try:
            if self.session_id:
                await client.beta.realtime.sessions.delete(self.session_id)
                print(f"[SUCCESS] Cleaned up session: {self.session_id}")
        except Exception as e:
            print(f"[ERROR] Failed to cleanup session: {e}")


# Global instance for the voice assistant
voice_assistant = RealtimeVoiceAssistant()

async def create_realtime_session(page_context: str, page_title: str):
    """
    Creates a new Realtime session and returns the client secret
    """
    client_secret = await voice_assistant.create_session(page_context, page_title)
    return client_secret

async def connect_realtime_session(client_secret: str):
    """
    Connects to an existing Realtime session
    """
    return await voice_assistant.connect_to_session(client_secret)

async def send_audio_to_realtime(audio_data: bytes):
    """
    Sends audio data to the Realtime session
    """
    return await voice_assistant.send_audio(audio_data)

async def commit_realtime_audio():
    """
    Commits audio buffer to trigger processing
    """
    return await voice_assistant.commit_audio()

async def disconnect_realtime():
    """
    Disconnects from the Realtime session
    """
    await voice_assistant.disconnect()

async def cleanup_realtime_session():
    """
    Cleans up the Realtime session
    """
    await voice_assistant.cleanup_session()
