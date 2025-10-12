import os
import sounddevice as sd
import numpy as np
import wave
import dotenv
import threading
import queue
import time
from openai import OpenAI, AsyncOpenAI 

# --- Configuration ---
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Check if the API key is available
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please set it in your .env file.")

# --- Clients for different contexts ---
# Sync client for the command-line part of the script
sync_client = OpenAI(api_key=OPENAI_API_KEY)
# Async client for use with FastAPI
async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def transcribe_audio_file(audio_file, filename: str):
    """
    Transcribes an audio file using OpenAI's Whisper model.
    """
    try:
        # The OpenAI library can take a tuple of (filename, file_content)
        # to correctly identify the file type.
        transcription = await async_client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, audio_file.read()),
        )
        return transcription.text
    except Exception as e:
        print(f"[ERROR] STT failed in async function: {e}")
        return None



# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1024  # Smaller block size for more responsive detection
DTYPE = 'int16'

# Detection settings
PAUSE_DURATION_SECONDS = 1.0  # How long of a silence triggers transcription
SILENCE_THRESHOLD = 300  # Adjust this based on your microphone's noise level
TEMP_AUDIO_FILE = "temp_input.wav"

# Global state
audio_buffer = []
is_speaking = False
silent_chunks_count = 0
stt_result_queue = queue.Queue()
stop_listening_flag = False


def transcribe_and_queue_sync(filename):
    """Transcribes saved audio using OpenAI API (sync version for CLI)."""
    print("\n[INFO] Transcribing speech...")
    try:
        with open(filename, "rb") as f:
            response = sync_client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        stt_result_queue.put(response.text)
    except Exception as e:
        print(f"[ERROR] Transcription failed: {e}")
        stt_result_queue.put(None)


def save_and_transcribe():
    """Saves the current buffer to a WAV and starts transcription."""
    global audio_buffer
    if not audio_buffer:
        return

    full_audio_data = np.concatenate(audio_buffer, axis=0)
    audio_buffer = []

    with wave.open(TEMP_AUDIO_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2) # 2 bytes for int16
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(full_audio_data.tobytes())

    threading.Thread(target=transcribe_and_queue_sync, args=(TEMP_AUDIO_FILE,), daemon=True).start()


def listen_once():
    """Listen for one phrase and return transcription."""
    global audio_buffer, is_speaking, silent_chunks_count, stop_listening_flag
    audio_buffer = []
    is_speaking = False
    silent_chunks_count = 0
    stop_listening_flag = False
    
    # Clear the queue before starting
    while not stt_result_queue.empty():
        stt_result_queue.get()

    def audio_callback(indata, frames, time_info, status):
        """Callback called by sounddevice for each chunk."""
        global is_speaking, silent_chunks_count, audio_buffer, stop_listening_flag

        # Use absolute values for RMS calculation
        volume_rms = np.sqrt(np.mean(np.abs(indata.astype(np.float32)) ** 2))
        is_sound = volume_rms > SILENCE_THRESHOLD

        if is_sound:
            if not is_speaking:
                print("[INFO] Speaking detected...", end='', flush=True)
            is_speaking = True
            silent_chunks_count = 0
            audio_buffer.append(indata.copy())
        elif is_speaking:
            print(".", end='', flush=True)
            audio_buffer.append(indata.copy()) # Continue recording during brief pauses
            silent_chunks_count += 1
            num_pause_blocks = int((PAUSE_DURATION_SECONDS * SAMPLE_RATE) / BLOCK_SIZE)
            if silent_chunks_count > num_pause_blocks:
                print("\n[INFO] Silence detected. Finishing...")
                stop_listening_flag = True

    print("\n" + "="*50)
    print("[INFO] Listening... Speak now.")
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        blocksize=BLOCK_SIZE,
        callback=audio_callback
    ):
        while not stop_listening_flag:
            time.sleep(0.1)

    # Save and transcribe after speech ends
    save_and_transcribe()

    # Wait for transcription thread
    result = None
    try:
        result = stt_result_queue.get(timeout=10) # 10-second timeout
    except queue.Empty:
        print("[WARN] Transcription timed out.")

    return result


if __name__ == "__main__":
    print("🎙️  Continuous Voice Transcription Started (press Ctrl+C to stop)\n")
    try:
        while True:
            text = listen_once()
            if text:
                print(f"\n🗣️  Transcription: {text.strip()}\n")
            else:
                print("\n[WARN] No speech detected or transcription failed.\n")
            print("-" * 60)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user. Exiting gracefully.")
    finally:
        if os.path.exists(TEMP_AUDIO_FILE):
            os.remove(TEMP_AUDIO_FILE)
