# FastAPI app usage

This library also provides a rough async FastAPI app. Code usage is seen below.

STEP 1: Installation and running the app:
```
# Install necessary libraries
pip install fastapi uvicorn

# run app, found in app.py
uvicorn app:app --reload
```



The app should be running in port 8000 by default.
STEP 2: set voices, currently a rough implementation. Will improve later on.
```
# Register the voice file and capture the output (which includes the user_id).
# Replace 'my_reference_audio.wav' with your actual filename.
#
# Try to manually copy the "user_id" from the output.
# For example, if the output is {"user_id": "929302"}, use that ID below.

curl -X 'GET' \
  'http://127.0.0.1:8000/set_voice/?audio_file=my_reference_audio.wav' \
  -H 'accept: application/json'
```



STEP 3: Run the model:
```
USER_ID="929302"  # Use the SAME user id you got from step 2
TEXT_TO_SAY="Hello, this is my custom cloned voice being streamed in real time."

# 2. POST request to stream the raw PCM audio and save it to a file
curl -X 'POST' \
  'http://127.0.0.1:8000/v1/audio/speech' \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "input": "'"$TEXT_TO_SAY"'",
    "voice": "'"$USER_ID"'",
    "model": "tts-1",
    "response_format": "pcm"
  }' \
  --output "output_audio.raw"

# The api will output 16 bit, 24khz, mono channel audio.
```
