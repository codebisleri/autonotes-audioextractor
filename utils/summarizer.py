from transformers import pipeline

# Load pre-trained summarization pipeline (can take 10–20 secs the first time)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def get_summary(text):
    if len(text) < 100:
        return "Text too short to summarize."
    
    # Limit input for large transcripts
    max_input_length = 1024
    text = text[:max_input_length]

    summary = summarizer(text, max_length=130, min_length=40, do_sample=False)
    return summary[0]['summary_text']
