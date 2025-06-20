from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from utils.transcriber import transcribe_audio  # Importing your transcribe_audio function
from utils.summarizer import get_summary
from reportlab.pdfgen import canvas
from deep_translator import GoogleTranslator
from moviepy import VideoFileClip
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # use os.urandom(24) to generate one

# ✅ DB Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
 
# ✅ File Upload Folder and Allowed Extensions
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ✅ DB Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    notes = db.relationship('Note', backref='owner')

# ✅ DB Model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transcript = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# ✅ Home Page + Upload Handler
@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        choice = request.form.get("feature")
        if choice == "autonotes":
            return redirect(url_for("autonotes_generator"))
        elif choice == "extract_audio":
            return redirect(url_for("extract_audio"))

    return render_template("index.html")

# ✅ Download as PDF
@app.route("/download", methods=["POST"])
def download_pdf():
    transcript = request.form["transcript"]
    summary = request.form["summary"]

    filename = "AutoNotes_Summary.pdf"
    filepath = os.path.join("uploads", filename)

    c = canvas.Canvas(filepath)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 800, "AutoNotes Summary")
    c.setFont("Helvetica", 10)

    y = 770
    for line in summary.split('\n'):
        c.drawString(50, y, line)
        y -= 15

    c.save()
    return send_file(filepath, as_attachment=True)

# ✅ View History Route
@app.route("/history")
def history():
    notes = Note.query.order_by(Note.date_created.desc()).all()
    return render_template("history.html", notes=notes)

from wordcloud import WordCloud
import matplotlib.pyplot as plt

@app.route("/wordcloud/<int:note_id>")
def wordcloud(note_id):
    note = Note.query.get_or_404(note_id)
    wc = WordCloud(width=800, height=400, background_color='white').generate(note.transcript)
    img_path = f"static/wordcloud_{note_id}.png"
    wc.to_file(img_path)
    return render_template("wordcloud.html", image_path=img_path)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash("Registered successfully! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("index"))

        flash("Invalid credentials!")
        return redirect(url_for("login"))

    return render_template("login.html")

# ✅ AutoNotes Generator (with multi-language support)
@app.route("/autonotes-generator", methods=["GET", "POST"])
def autonotes_generator():
    if "user_id" not in session:
        return redirect(url_for("login"))

    transcript = ""
    summary = ""
    translated_transcript = ""
    translated_summary = ""
    selected_lang = "en"  # default to English

    if request.method == "POST":
        selected_lang = request.form.get("language", "en")

        if 'audio' in request.files:
            file = request.files["audio"]
            audio_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(audio_path)

            # Transcribe the audio
            transcript = transcribe_audio(audio_path)
            summary = get_summary(transcript)

            # Debugging: Print the selected language code
            print(f"Selected language code: {selected_lang}")

            # Correct the language code if necessary
            if "-" in selected_lang:
                selected_lang = selected_lang.split("-")[0]  # Keep only the first part (e.g., "en")
                print(f"Corrected language code: {selected_lang}")

            # Translate the transcript and summary if needed
            if selected_lang != "en":
                try:
                    translated_transcript = GoogleTranslator(
                        source='auto', target=selected_lang).translate(transcript)
                    translated_summary = GoogleTranslator(
                        source='auto', target=selected_lang).translate(summary)
                except Exception as e:
                    flash(f"Error during translation: {e}", "error")
                    # Optionally, you could set translated_transcript and translated_summary to the original
                    translated_transcript = transcript
                    translated_summary = summary
            else:
                translated_transcript = transcript
                translated_summary = summary

            # Save to database
            new_note = Note(
                transcript=transcript, summary=summary, user_id=session["user_id"])
            db.session.add(new_note)
            db.session.commit()

    return render_template("autonotes_generator.html",
                           transcript=transcript,
                           summary=summary,
                           translated_transcript=translated_transcript,
                           translated_summary=translated_summary,
                           selected_lang=selected_lang)

# ✅ Extract Audio from Video
@app.route('/extract-audio', methods=['GET', 'POST'])
def extract_audio():
    if request.method == 'POST':
        video = request.files['video']
        if video:
            video_filename = secure_filename(video.filename)
            video_path = os.path.join('uploads', video_filename)
            video.save(video_path)

            # Load video and extract audio
            clip = VideoFileClip(video_path)
            audio_filename = os.path.splitext(video_filename)[0] + ".mp3"
            audio_path = os.path.join('static', audio_filename)
            clip.audio.write_audiofile(audio_path)

            # IMPORTANT: Close the VideoFileClip object to release the file handle.
            clip.close()

            # Remove video file after extraction (optional)
            try:
                os.remove(video_path)
            except Exception as e:
                print(f"Error removing video file: {e}") # Important: Log the error.  Don't just pass.
                flash(f"Error removing video file.  Please check the server logs.  The audio was still extracted.", 'error')

            # Return audio filename to template
            return render_template("extract_audio.html", audio_filename=audio_filename)

    return render_template("extract_audio.html")

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    transcript = data['transcript']
    summary = data['summary']
    language = data['language']

    translated_transcript = GoogleTranslator(
        source='auto', target=language).translate(transcript)
    translated_summary = GoogleTranslator(
        source='auto', target=language).translate(summary)

    return jsonify({
        'translated_transcript': translated_transcript,
        'translated_summary': translated_summary
    })


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ✅ Run the app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Creates DB tables if not exist
    app.run(debug=True)