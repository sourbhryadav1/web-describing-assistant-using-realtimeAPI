import os
from openai import AsyncOpenAI  # Use the async client for FastAPI
import dotenv
from pathlib import Path

# --- Configuration ---
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Check if the API key is available
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please set it in your .env file.")

# Use the async client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def text_to_speech_stream(text_to_speak: str, model: str = "tts-1", voice: str = "shimmer"):
    """
    Converts text into an audio stream using OpenAI's TTS API.
    This is an async generator that yields audio chunks.
    """
    try:
        response = await client.audio.speech.create(
            model=model,
            voice=voice,
            input=text_to_speak
        )
        # FIX: The aiter_bytes() method is a coroutine and must be awaited
        async for chunk in await response.aiter_bytes():
            yield chunk

    except Exception as e:
        print(f"\n[ERROR] Failed to generate speech: {e}")
        yield b""

async def chat_with_openai(user_prompt: str, system_prompt: str = "You are a helpful assistant, ans not more than 50 words."):
    """
    Sends a text prompt to OpenAI's chat API and gets a text response.

    Args:
        user_prompt (str): The user's message.
        system_prompt (str): The system instruction to guide the assistant's behavior.

    Returns:
        str: The assistant's text response, or None if an error occurs.
    """
    try:
        print("\n[INFO] Getting response from OpenAI chat...")
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        assistant_response = response.choices[0].message.content
        print("[SUCCESS] Response received.")
        return assistant_response
    except Exception as e:
        print(f"[ERROR] Failed to chat with OpenAI: {e}")
        return None


if __name__ == "__main__":
    # Note: The main execution block here is for testing and uses synchronous methods.
    # The async functions are designed to be called from an async environment like FastAPI.
    print("This file provides async utility functions for a web server.")
    print("To test, you would typically run them inside an asyncio event loop.")

