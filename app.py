from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Form
import aiohttp
import websockets
import asyncio
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from bs4 import BeautifulSoup
import os, io
from starlette.responses import JSONResponse
from openai import AsyncOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
import json
from fastapi import UploadFile, File
import tempfile

from stt import transcribe_audio_file
from tts import chat_with_openai, text_to_speech_stream
from realtime import create_realtime_session

# --- Pydantic Model for Incoming Requests ---
class PageRequest(BaseModel):
    page_name: str

# Load environment variables from a .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- OpenAI Initialization ---
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Default Instructions for the Real-time Agent ---
DEFAULT_INSTRUCTIONS = "You are a friendly and helpful voice assistant. Be conversational and concise in your responses."
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

# --- FastAPI App Initialization ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CORE LOGIC: Parse HTML to get plain text ---
def get_structured_page_data_for_summarize_and_speak(filename: str):
    """
    Reads index.html and extracts structured data about its purpose,
    navigation, and actions.
    """
    file_path = os.path.join(BASE_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found at path '{file_path}'.")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'lxml')


        # Extract key pieces of information dynamically
        title = soup.find('title').get_text(strip=True) if soup.find('title') else "Untitled Page"
        
        # Find all navigation links
        all_nav_links = []
        for nav in soup.find_all('nav'):
            all_nav_links.extend([a.get_text(strip=True) for a in nav.find_all('a')])
        
        # Find all headings to identify main topics
        main_topics = [h.get_text(strip=True) for h in soup.find('main').find_all(['h2', 'h3'])] if soup.find('main') else []
        
        # Find all potential action buttons/links
        actions = [btn.get_text(strip=True) for btn in soup.find_all(['button', 'a']) if btn.get('class') and ('bg-blue-600' in btn.get('class') or 'bg-green-600' in btn.get('class'))]

        # Combine the data into a context string for the AI
        context = f"""
        - Page Title: "{title}"
        - Main Topics Covered: {', '.join(main_topics) or "N/A"}
        - Available Navigation Links: {', '.join(list(set(all_nav_links))) or "N/A"}
        - Potential Actions on Page: {', '.join(actions) or "N/A"}
        """
        return context, title

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while parsing HTML: {str(e)}")


def get_structured_page_data_for_realtime(filename: str):
    """
    Extracts a comprehensive set of details from the HTML content of a webpage.
    """
    file_path = os.path.join(BASE_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found at path '{file_path}'.")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')

        # 1. Page Title (already good)
        title = soup.find('title').get_text(strip=True) if soup.find('title') else "Untitled Page"

        # 2. Meta Information (Description and Keywords are very important)
        description = soup.find('meta', attrs={'name': 'description'})
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        
        meta_description = description['content'] if description and description.has_attr('content') else "N/A"
        meta_keywords = keywords['content'] if keywords and keywords.has_attr('content') else "N/A"

        # 3. All Headings (h1 through h6) to understand structure
        all_headings = {f'h{i}': [] for i in range(1, 7)}
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                all_headings[f'h{i}'].append(heading.get_text(strip=True))

        # 4. All Links on the entire page, not just in <nav>
        # We store them in a dictionary to keep text and URL together
        all_links = {}
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            href = link['href']
            if text and href and not href.startswith('#'): # Ignore empty text and anchor links
                all_links[text] = href

        # 5. Extract all plain text content for context
        # Use a separator to make the text more readable
        full_text_content = soup.get_text(separator='\n', strip=True)

        # 6. Extract Image Descriptions (alt text) for accessibility and context
        image_descriptions = [img['alt'] for img in soup.find_all('img') if img.has_attr('alt') and img['alt']]

        # 7. A more robust way to find "Actions"
        # Look for buttons and links styled as buttons (e.g., role="button")
        potential_actions = []
        for action_tag in soup.find_all(['button', 'a']):
            text = action_tag.get_text(strip=True)
            if not text:
                continue
            # Check if it's a button tag or an 'a' tag with a button-like role or class
            if action_tag.name == 'button' or (action_tag.has_attr('role') and 'button' in action_tag['role']):
                potential_actions.append(text)
        
        # --- Combine data into a more structured dictionary ---
        context = {
            "title": title,
            "meta_description": meta_description,
            "meta_keywords": meta_keywords,
            "headings": all_headings,
            "links": all_links,
            "image_alt_texts": list(set(image_descriptions)), # Use set to get unique descriptions
            "actions": list(set(potential_actions)), # Use set to get unique actions
            "full_text": full_text_content
        }
        
        return context, title
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while parsing HTML: {str(e)}")


# --- NEW ENDPOINT: Summarize Text and Convert to Speech ---
@app.post("/summarize-and-speak")
async def summarize_and_speak(request: PageRequest):
    print(f"Request received for page: {request.page_name}")
    page_context, page_title = get_structured_page_data_for_summarize_and_speak(request.page_name)

    prompt_1_system = """
    You are an expert content analyst. Your task is to create a detailed, structured knowledge summary from a webpage's data. 
    This summary will be the sole source of truth for a conversational voice assistant.
    Synthesize the provided information into a factual knowledge base. Use the following headings:
    ### Page Purpose
    [Briefly state the main goal or topic of this page.]
    ### Navigation Options
    [List all available navigation links and their likely purpose.]
    ### Key Content
    [Describe the primary topics, sections, and data points mentioned on the page.]
    ### User Actions
    [Detail any interactive elements like buttons or forms and what they do.]
    """

    detailed_knowledge_base = await chat_with_openai(f"Page info:\n{page_context}", system_prompt=prompt_1_system)
    if not detailed_knowledge_base:
        raise HTTPException(status_code=500, detail="Failed to generate knowledge base.")
    print("[SUCCESS] Detailed knowledge base created.")
    # For debugging
    # print(f"--- KNOWLEDGE BASE ---\n{detailed_knowledge_base}\n--------------------")
    
    prompt_2_system = f"""
    You are a friendly voice assistant. Your goal is to give a quick, helpful overview of the current page, '{page_title}'. 
    Use the provided 'PAGE KNOWLEDGE BASE' to generate a spoken welcome message that must be less than 10 seconds long.
    Your message should cover what the page is about and what the user can do must include the navigation options and headers. 
    Be conversational and end your message with the exact phrase: 'how may I assist you today?'
    ---
    PAGE KNOWLEDGE BASE:
    {detailed_knowledge_base}
    ---
    """
    conversational_summary_text = await chat_with_openai("Generate the welcome message now.", system_prompt=prompt_2_system)
    if not conversational_summary_text:
        raise HTTPException(status_code=500, detail="Failed to get summary from chat model.")

    print(f"[SUCCESS] Guided summary received: {conversational_summary_text}")
    
    audio_stream_generator = text_to_speech_stream(conversational_summary_text)
    
    print("Audio generated. Streaming response to client.")
    return StreamingResponse(audio_stream_generator, media_type="audio/mpeg")


@app.post("/create-talk-session")
async def create_talk_session(request: PageRequest):
    """
    Creates a real-time session with OpenAI and returns the client_secret 
    for the frontend to connect directly.
    """
    print(f"Creating Realtime session for page: {request.page_name}")
    
    try:
        # Get page context for the session
        page_context, page_title = get_structured_page_data_for_realtime(request.page_name)
        
        # Create Realtime session with page-specific context
        session_info = await create_realtime_session(page_context, page_title)
        
        if not session_info:
            raise HTTPException(status_code=500, detail="Failed to create OpenAI Realtime session")

        print(f"Successfully created Realtime session. Returning session info.")
        return JSONResponse(session_info)

    except Exception as e:
        print(f"An unexpected error occurred in session creation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/realtime")
async def websocket_proxy(websocket: WebSocket):
    """
    WebSocket proxy that handles authentication with OpenAI Realtime API
    """
    await websocket.accept()
    
    try:
        # Receive the client_secret, model, and page info from the client
        init_message = await websocket.receive_text()
        import json
        init_data = json.loads(init_message)
        client_secret = init_data.get("client_secret")
        model = init_data.get("model", "gpt-realtime")
        page_name = init_data.get("page_name", "index.html")
        
        if not client_secret:
            await websocket.send_text(json.dumps({"error": "Missing client_secret"}))
            await websocket.close()
            return
        
        print(f"[INFO] Connecting to OpenAI Realtime API with client_secret: {client_secret}, model: {model}")
        
        # Get page context for instructions
        page_context, page_title = get_structured_page_data_for_realtime(page_name)
        
        # Connect to OpenAI Realtime API with authentication using main API key
        # Note: The ephemeral session approach seems to have version mismatch issues
        # Using direct API key authentication instead
        openai_ws_url = f"wss://api.openai.com/v1/realtime?model={model}"
        
        # Required headers for Realtime API
        extra_headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        async with websockets.connect(
            openai_ws_url,
            additional_headers=extra_headers,
            open_timeout=30,
            close_timeout=10
        ) as openai_ws:
            print("[SUCCESS] Connected to OpenAI Realtime API")
            
            # Send session configuration with page-specific instructions
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": f"""You are a helpful voice assistant for the webpage '{page_title}'. 
                    Your knowledge is strictly limited to the information provided below.

                    PAGE CONTEXT:
                    {page_context}

                    Rules:
                    1. Be brief but complete - keep responses under 7 seconds,  and make it as to the point as possible.
                    2. Only answer questions about the page content above
                    3. If asked about anything not on this page, say: "I can only answer questions about the content on this page. You could ask me about our core technologies, for example."
                    4. Be conversational and helpful
                    5. Always give responce to the point not a long story.
                    6. If the user language is hindi, speek hindi but not perfect hindi that user wont understand, use basic hindi only.
                    """,
                    "voice": "shimmer",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 200
                    },
                    "temperature": 0.8,
                    "max_response_output_tokens": 500
                }
            }
            await openai_ws.send(json.dumps(session_config))
            print("[INFO] Sent session configuration to OpenAI")
            
            # Create tasks for bidirectional communication
            async def forward_to_openai():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await openai_ws.send(data)
                except Exception as e:
                    print(f"[ERROR] Forward to OpenAI error: {e}")
            
            async def forward_to_client():
                try:
                    async for message in openai_ws:
                        await websocket.send_text(message)
                except Exception as e:
                    print(f"[ERROR] Forward to client error: {e}")
            
            # Run both tasks concurrently
            await asyncio.gather(
                forward_to_openai(),
                forward_to_client()
            )
    
    except WebSocketDisconnect:
        print("[INFO] Client disconnected")
    except Exception as e:
        print(f"[ERROR] WebSocket proxy error: {e}")
        try:
            await websocket.close()
        except:
            pass

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI backend for the voice assistant!"}

# --- Server Execution ---
if __name__ == "__main__":
    # For development, run with: uvicorn app:app --reload
    uvicorn.run(app, host="127.0.0.1", port=5000)

