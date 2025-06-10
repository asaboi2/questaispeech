# Real-time AI Assistant

This project implements a real-time AI assistant that uses AssemblyAI for speech-to-text, Gemini for language processing, and Hume for text-to-speech.

## Prerequisites

*   API keys for AssemblyAI, Google Gemini, and Hume.
*   Python 3.6 or higher.
*   `pyaudio` may require additional system-level dependencies (e.g., `portaudio`).

## Installation

1.  Clone the repository:

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3.  Set the API keys as environment variables:

    ```bash
    export ASSEMBLYAI_API_KEY="your_assemblyai_key"
    export GOOGLE_API_KEY="your_gemini_key"
    export HUME_API_KEY="your_hume_key"
    ```

    Or, in Windows:

    ```bash
    set ASSEMBLYAI_API_KEY="your_assemblyai_key"
    set GOOGLE_API_KEY="your_gemini_key"
    set HUME_API_KEY="your_hume_key"
    ```

## Usage

1.  **Set the Hume Custom Voice ID:**
    *   Open the `realtime_agent.py` file.
    *   Locate the `hume_tts_speaker` function.
    *   Find the line `HUME_CUSTOM_VOICE_ID = "YOUR_VOICE_ID"` and replace `"YOUR_VOICE_ID"` with your Hume voice ID (e.g., `"57bbe070-a935-4eae-9796-937fb2042292"`).

2.  Run the script:

    ```bash
    python realtime_agent.py
    ```

Speak into your microphone. The AI will respond when you pause.

## Deployment to Railway

1.  Create a Railway account and project.
2.  Install the Railway CLI:

    ```bash
    npm install -g @railway/cli
    ```

3.  Log in to Railway:

    ```bash
    railway login
    ```

4.  Initialize a Railway project:

    ```bash
    railway init
    ```

5.  Configure the environment variables in the Railway dashboard.
6.  Deploy the project:

    ```bash
    railway up
    ```

## Notes

*   This setup will have a latency of roughly 800ms - 1.5s.
*   Be mindful that you are running three paid, streaming services simultaneously.
*   This script has basic error handling. A production system would need more sophisticated logic.
*   This implementation does not handle "barge-in".
