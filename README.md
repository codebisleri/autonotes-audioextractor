# autonotes-audioextractor

AutoNotes is a smart AI-powered web application that:
- Transcribes speech from **audio or video files**
- Extracts **audio from videos**
- Generates **summarized notes**
- Supports **multi-language translation** (optional)
  
---

## 🔧 Features

- 🎤 **Audio & Video Transcription** using OpenAI's Whisper
- ✂️ **Audio Extraction** from video files (e.g., MP4, MOV)
- 📝 **Automatic Note Summarization** with HuggingFace Transformers
- 🌐 **Multi-language Translation** using Deep Translator
- 📄 Export to PDF
- 🧠 WordCloud from transcripts
- 🔐 User registration, login, and transcript history

---

## 🚀 How to Run Locally

```bash
git clone https://github.com/codebisleri/autonotesgenerator.git
cd autonotesgenerator

# Create virtual environment
python -m venv venv
venv\Scripts\activate      # On Windows
# Or use: source venv/bin/activate (on Mac/Linux)

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env       # Or create your own .env file
# Make sure it includes a SECRET_KEY

# Run the app
python app.py

Then open your browser at: http://localhost:5000
