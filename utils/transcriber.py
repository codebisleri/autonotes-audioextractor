# import whisper

# # Load the pre-trained model
# model = whisper.load_model("base")  # You can try "small", "medium" for better accuracy

# def transcribe_audio(audio_path, language_code='en'):
#     print(f"Transcribing {audio_path} in {language_code}")
    
#     result = model.transcribe(audio_path)  # Process the audio file using Whisper model
    
#     transcript = result["text"]
#     return transcript

# In utils/transcriber.py
import whisper
import torch

# Load the pre-trained model
model = whisper.load_model("small") #or "tiny"# You can try "small", "medium" for better accuracy

def transcribe_audio(audio_path):
    print(f"Transcribing {audio_path}")
    try:
        result = model.transcribe(audio_path)  # Process the audio file using Whisper model
        transcript = result["text"]
        return transcript
    except RuntimeError as e:
        print(f"Error transcribing audio: {e}")
        return ""  # Or you might want to raise the exception, or return a default value
    except torch.cuda.OutOfMemoryError as e:
        print(f"Ran out of VRAM, try a smaller model: {e}")
        return ""