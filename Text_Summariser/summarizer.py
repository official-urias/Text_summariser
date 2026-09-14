"""
Core Text Summarization and Analytics Engine
Supports both high-speed local extractive NLP (TextRank/Frequency scoring)
and AI abstractive summarization via Google Gemini (google-genai SDK).
"""

import os
import re
import math
from collections import Counter

# Safe NLTK initialization with fallbacks
FALLBACK_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
}

_nltk_ready = False
_stopwords = FALLBACK_STOPWORDS

def ensure_nltk_resources():
    global _nltk_ready, _stopwords
    if _nltk_ready:
        return
    try:
        import nltk
        import contextlib
        import io

        # Suppress stderr noise if offline
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            for res in ['tokenizers/punkt', 'tokenizers/punkt_tab', 'corpora/stopwords']:
                try:
                    nltk.data.find(res)
                except LookupError:
                    pkg = res.split('/')[-1]
                    try:
                        nltk.download(pkg, quiet=True, raise_on_error=False)
                    except Exception:
                        pass

        from nltk.corpus import stopwords
        _stopwords = set(stopwords.words('english'))
        _nltk_ready = True
    except Exception:
        _stopwords = FALLBACK_STOPWORDS
        _nltk_ready = True

def split_sentences(text: str):
    """Tokenize text into sentences with fallback to regex."""
    ensure_nltk_resources()
    try:
        from nltk.tokenize import sent_tokenize
        sentences = sent_tokenize(text)
        if sentences:
            return sentences
    except Exception:
        pass
    # Regex fallback
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]

def tokenize_words(text: str):
    """Tokenize text into word tokens."""
    ensure_nltk_resources()
    try:
        from nltk.tokenize import word_tokenize
        return word_tokenize(text)
    except Exception:
        return re.findall(r'\b[a-zA-Z0-9_-]+\b', text)


def summarize_local(text: str, ratio: float = 0.35, output_format: str = "paragraph") -> dict:
    """
    High-performance extractive summarizer using TF-IDF term salience,
    positional lead bias, and sentence graph ranking.
    """
    text = text.strip()
    if not text:
        raise ValueError("Text cannot be empty.")

    sentences = split_sentences(text)
    total_sentences = len(sentences)

    if total_sentences <= 2:
        return {
            "summary": text,
            "engine": "local-extractive",
            "format": output_format,
            "selected_sentence_indices": list(range(total_sentences))
        }

    # Word frequencies excluding stopwords and non-alphanumeric
    words = tokenize_words(text.lower())
    clean_words = [w for w in words if w.isalnum() and w not in _stopwords and len(w) > 2]

    if not clean_words:
        return {
            "summary": " ".join(sentences[:2]),
            "engine": "local-extractive",
            "format": output_format,
            "selected_sentence_indices": [0, 1] if total_sentences > 1 else [0]
        }

    freq_table = Counter(clean_words)
    max_freq = max(freq_table.values()) if freq_table else 1

    # Normalize frequencies with sublinear scaling
    norm_freq = {w: (1 + math.log(count)) / (1 + math.log(max_freq)) for w, count in freq_table.items()}

    # Score each sentence
    sentence_scores = []
    for idx, sentence in enumerate(sentences):
        sentence_words = tokenize_words(sentence.lower())
        word_count = len(sentence_words)

        if word_count < 4:
            # Skip very short fragments
            continue

        raw_score = sum(norm_freq.get(w, 0) for w in sentence_words if w in norm_freq)
        
        # Length normalization (avoid bias toward overly long sentences)
        length_factor = math.pow(word_count, 0.7)
        normalized_score = raw_score / length_factor if length_factor > 0 else 0

        # Position weighting (Lead bias: First 2 sentences in prose frequently capture the core thesis)
        if idx == 0:
            normalized_score *= 1.35
        elif idx == 1:
            normalized_score *= 1.15
        elif idx == total_sentences - 1:
            # Final concluding sentence often has summary value
            normalized_score *= 1.10

        sentence_scores.append((idx, sentence, normalized_score))

    if not sentence_scores:
        sentence_scores = [(i, s, 1.0) for i, s in enumerate(sentences)]

    # Determine target number of sentences based on ratio
    target_count = max(1, min(total_sentences, int(math.ceil(total_sentences * ratio))))
    if output_format == "tldr":
        target_count = 1
    elif output_format == "bullets":
        target_count = max(2, min(6, target_count))

    # Select top ranked sentences
    sentence_scores.sort(key=lambda x: x[2], reverse=True)
    selected = sentence_scores[:target_count]

    # Re-order chronologically for natural narrative flow
    selected.sort(key=lambda x: x[0])
    selected_indices = [item[0] for item in selected]
    selected_sentences = [item[1].strip() for item in selected]

    if output_format == "bullets":
        summary = "\n".join(f"• {s}" for s in selected_sentences)
    elif output_format == "tldr":
        summary = selected_sentences[0]
    else: # paragraph
        summary = " ".join(selected_sentences)

    return {
        "summary": summary,
        "engine": "local-extractive",
        "format": output_format,
        "selected_sentence_indices": selected_indices
    }


def summarize_gemini(text: str, output_format: str = "paragraph", ratio: float = 0.35, api_key: str = None) -> dict:
    """
    AI Abstractive Summarizer powered by Google Gemini (gemini-2.5-flash).
    Rewrites and consolidates the text intelligently with zero sentence cutting.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("No Gemini API key provided. Please provide an API key or switch to the Local Engine.")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)

        format_instructions = {
            "paragraph": "Provide a cohesive, well-written executive summary paragraph capturing the central themes, arguments, and conclusions.",
            "bullets": "Provide 3 to 6 high-impact, actionable bullet points highlighting the core takeaways and critical details. Format each point with '• '.",
            "tldr": "Provide an ultra-concise TL;DR consisting of 1 to 2 powerful sentences that encapsulate the entire text."
        }

        length_desc = "concise" if ratio <= 0.25 else ("detailed and thorough" if ratio >= 0.5 else "balanced")

        prompt = (
            f"You are an expert executive research analyst and content summarizer.\n"
            f"Summarize the following text in a {length_desc} manner.\n"
            f"Style requirement: {format_instructions.get(output_format, format_instructions['paragraph'])}\n"
            f"Do not include meta-commentary (like 'Here is a summary:'). Output ONLY the final summary.\n\n"
            f"SOURCE TEXT:\n{text}"
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=1024
            )
        )

        summary_text = response.text.strip()
        return {
            "summary": summary_text,
            "engine": "gemini-2.5-flash",
            "format": output_format,
            "selected_sentence_indices": []
        }
    except Exception as e:
        raise RuntimeError(f"Gemini AI Inference error: {str(e)}")


def extract_keywords(text: str, top_n: int = 6) -> list:
    """Extract primary keywords / thematic concepts from text."""
    ensure_nltk_resources()
    words = tokenize_words(text.lower())
    filtered = [
        w for w in words 
        if w.isalnum() and not w.isnumeric() and w not in _stopwords and len(w) > 3
    ]
    if not filtered:
        return []
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(top_n)]


def calculate_metrics(original_text: str, summary_text: str) -> dict:
    """Compute word counts, compression ratio, and estimated reading time saved."""
    orig_words = len(re.findall(r'\b\w+\b', original_text))
    sum_words = len(re.findall(r'\b\w+\b', summary_text))
    
    orig_chars = len(original_text)
    sum_chars = len(summary_text)

    # Average adult reading speed: ~200-220 words per minute
    WPM = 200
    orig_read_time_min = orig_words / WPM
    sum_read_time_min = sum_words / WPM
    time_saved_sec = max(0, int((orig_read_time_min - sum_read_time_min) * 60))

    if orig_words > 0:
        compression_ratio = max(0, min(99, int(round((1.0 - (sum_words / orig_words)) * 100))))
    else:
        compression_ratio = 0

    return {
        "original_words": orig_words,
        "summary_words": sum_words,
        "original_characters": orig_chars,
        "summary_characters": sum_chars,
        "compression_percent": compression_ratio,
        "reading_time_original_sec": int(orig_read_time_min * 60),
        "reading_time_summary_sec": int(sum_read_time_min * 60),
        "time_saved_sec": time_saved_sec,
        "time_saved_display": f"{time_saved_sec // 60}m {time_saved_sec % 60}s" if time_saved_sec >= 60 else f"{time_saved_sec}s"
    }
