import os
import asyncio
import pyaudio
import websockets
import json
import base64
from hume import HumeStreamClient, HumeClientException
from hume.models.config import ProsodyConfig
import google.generativeai as genai

# --- Configuration ---
# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 8000

# API Keys from environment variables
AII_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
HUME_API_KEY = os.environ.get("HUME_API_KEY")

# Configure APIs
genai.configure(api_key=GOOGLE_API_KEY)
GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash')
SYSTEM_PROMPT = "You are a friendly, expressive, and empathetic AI assistant. Keep your responses concise, warm, and conversational."

# --- Queues for Inter-thread Communication ---
# We use asyncio queues for safe data sharing between our async tasks
transcript_queue = asyncio.Queue()
llm_response_queue = asyncio.Queue()

class AudioPlayer:
    """Plays audio chunks received from Hume AI."""
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=24000, # Hume default output rate
                                  output=True)

    def play(self, audio_chunk):
        """Plays a single chunk of audio."""
        self.stream.write(audio_chunk)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

async def assemblyai_listener():
    """Listens to the microphone and streams to AssemblyAI for real-time transcription."""
    print("Connecting to AssemblyAI...")
    uri = f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={RATE}"
    
    async with websockets.connect(
        uri,
        extra_headers={"Authorization": AII_API_KEY}
    ) as ws:
        await asyncio.sleep(0.1)
        print("Receiving from AssemblyAI...")

        p = pyaudio.PyAudio()
        mic_stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

        async def send_audio():
            while True:
                data = mic_stream.read(CHUNK)
                data = base64.b64encode(data).decode("utf-8")
                await ws.send(json.dumps({"audio_data": data}))
                await asyncio.sleep(0.01) # Small sleep to prevent busy-waiting

        async def receive_transcript():
            async for msg in ws:
                data = json.loads(msg)
                if data['message_type'] == 'FinalTranscript':
                    transcript = data['text']
                    if transcript:
                        print(f"User said: {transcript}")
                        await transcript_queue.put(transcript)

        send_task = asyncio.create_task(send_audio())
        receive_task = asyncio.create_task(receive_transcript())
        await asyncio.gather(send_task, receive_task)

async def gemini_processor():
    """Processes transcripts from the queue and streams responses from Gemini."""
    while True:
        transcript = await transcript_queue.get()
        print("Sending to Gemini...")
        
        # Start a chat session with history (optional but good practice)
        chat = GEMINI_MODEL.start_chat(history=[])
        
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {transcript}\nAI:"
        
        try:
            # Use stream=True to get responses chunk by chunk
            response_stream = chat.send_message(full_prompt, stream=True)
            for chunk in response_stream:
                if chunk.text:
                    print(f"Gemini chunk: {chunk.text}")
                    await llm_response_queue.put(chunk.text)
            # Signal the end of the response
            await llm_response_queue.put(None) 
        except Exception as e:
            print(f"Error with Gemini: {e}")
            await llm_response_queue.put(None) # Ensure we unblock the TTS

async def hume_tts_speaker():
    """Streams text from a queue to Hume AI and plays the resulting audio."""
    player = AudioPlayer()

    # --- THIS IS THE PART YOU CHANGE ---
    # Define the ID for your custom voice.
    # It's good practice to make this a variable at the top of your script.
    HUME_CUSTOM_VOICE_ID = "57bbe070-a935-4eae-9796-937fb2042292"  # <-- PASTE YOUR VOICE ID HERE

    while True:
        try:
            client = HumeStreamClient(HUME_API_KEY)
            config = ProsodyConfig(voice_id=HUME_CUSTOM_VOICE_ID, instant_generate=True)

            async with client.connect([config]) as socket:
                print("Hume TTS connected and ready.")

                # This inner loop handles one full AI utterance
                while True:
                    text_chunk = await llm_response_queue.get()
                    if text_chunk is None:  # End of response signal
                        break  # Break inner loop to wait for next user input

                    result = await socket.send_text(text_chunk)
                    if result and "audio_output" in result:
                        audio_output = result["audio_output"]
                        player.play(audio_output.get_bytes())

        except HumeClientException as e:
            print(f"Hume connection error: {e}. Reconnecting...")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"An unexpected error occurred in Hume TTS: {e}")
            break  # Exit on other critical errors

    player.close()

async def main():
    """The main function to orchestrate all the async tasks."""
    print("Starting AI Assistant...")
    print("Speak into your microphone. The AI will respond when you pause.")

    # Create and run all tasks concurrently
    listener_task = asyncio.create_task(assemblyai_listener())
    processor_task = asyncio.create_task(gemini_processor())
    speaker_task = asyncio.create_task(hume_tts_speaker())

    await asyncio.gather(listener_task, processor_task, speaker_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
