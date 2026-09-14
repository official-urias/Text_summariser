"""
AI Text Summarizer - Modern Hybrid Application
Dual Engine (Local Extractive NLP + Google Gemini AI)
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, render_template

# Ensure the app's directory is always in sys.path for direct and package imports
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Optional .env loading without external dependencies
_env_file = BASE_DIR.parent / '.env'
if _env_file.exists():
    try:
        with open(_env_file, 'r', encoding='utf-8') as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _k, _v = _line.split('=', 1)
                    os.environ.setdefault(_k.strip(), _v.strip().strip("'\""))
    except Exception:
        pass

try:
    from summarizer import (
        summarize_local,
        summarize_gemini,
        extract_keywords,
        calculate_metrics,
        ensure_nltk_resources
    )
    from scraper import extract_from_url, extract_from_file
except ImportError:
    from Text_Summariser.summarizer import (
        summarize_local,
        summarize_gemini,
        extract_keywords,
        calculate_metrics,
        ensure_nltk_resources
    )
    from Text_Summariser.scraper import extract_from_url, extract_from_file

# Resolve templates folder regardless of case sensitivity
template_dir = BASE_DIR / 'Templates' if (BASE_DIR / 'Templates').exists() else BASE_DIR / 'templates'

app = Flask(
    __name__,
    template_folder=str(template_dir),
    static_folder=str(BASE_DIR / 'static')
)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload limit

# Pre-warm NLTK resources in the background
ensure_nltk_resources()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online",
        "service": "AI Text Summarizer",
        "version": "2.0.0",
        "has_gemini_key": bool(os.environ.get("GEMINI_API_KEY"))
    })


@app.route('/api/summarize', methods=['POST'])
def handle_summarize():
    try:
        data = request.get_json(force=True, silent=True) or {}
        text = data.get('text', '').strip()
        engine = data.get('engine', 'local').lower()
        output_format = data.get('format', 'paragraph').lower()
        ratio = float(data.get('ratio', 0.35))
        api_key = data.get('api_key', '').strip() or None

        if not text:
            return jsonify({"error": "Please provide text to summarize."}), 400

        words = text.split()
        if len(words) < 10:
            return jsonify({"error": "Text is too brief. Please enter at least 10 words."}), 400

        # Validate format
        if output_format not in ['paragraph', 'bullets', 'tldr']:
            output_format = 'paragraph'

        # Clamp ratio between 0.15 and 0.70
        ratio = max(0.15, min(0.70, ratio))

        fallback_occurred = False
        fallback_reason = None
        result = None

        if engine == 'gemini':
            try:
                result = summarize_gemini(
                    text=text,
                    output_format=output_format,
                    ratio=ratio,
                    api_key=api_key
                )
            except Exception as e:
                # Graceful fallback to local engine
                fallback_occurred = True
                fallback_reason = str(e)
                result = summarize_local(
                    text=text,
                    ratio=ratio,
                    output_format=output_format
                )
        else:
            result = summarize_local(
                text=text,
                ratio=ratio,
                output_format=output_format
            )

        summary_text = result["summary"]
        metrics = calculate_metrics(text, summary_text)
        keywords = extract_keywords(text, top_n=8)

        response_payload = {
            "summary": summary_text,
            "engine": result["engine"],
            "format": result["format"],
            "fallback": fallback_occurred,
            "fallback_reason": fallback_reason,
            "metrics": metrics,
            "keywords": keywords,
            "selected_sentence_indices": result.get("selected_sentence_indices", [])
        }

        return jsonify(response_payload), 200

    except Exception as e:
        return jsonify({"error": f"Summarization failed: {str(e)}"}), 500


@app.route('/api/extract-url', methods=['POST'])
def handle_extract_url():
    try:
        data = request.get_json(force=True, silent=True) or {}
        url = data.get('url', '').strip()
        if not url:
            return jsonify({"error": "URL cannot be empty."}), 400

        extracted = extract_from_url(url)
        return jsonify(extracted), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except ConnectionError as ce:
        return jsonify({"error": str(ce)}), 502
    except Exception as e:
        return jsonify({"error": f"Failed to extract URL: {str(e)}"}), 500


@app.route('/api/upload', methods=['POST'])
def handle_upload():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded."}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected."}), 400

        extracted = extract_from_file(file)
        return jsonify(extracted), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Upload processing failed: {str(e)}"}), 500


if __name__ == '__main__':
    import webbrowser
    import threading

    port = int(os.environ.get('PORT', 5000))
    url = f"http://127.0.0.1:{port}"
    print(f"\n=======================================================")
    print(f"🚀 AI Text Summarizer v2.0 running at {url}")
    print(f"🌐 Opening default web browser automatically...")
    print(f"=======================================================\n")

    # Auto-open browser on launch (avoid duplicate tabs when Werkzeug reloads)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    app.run(host='0.0.0.0', port=port, debug=True)
