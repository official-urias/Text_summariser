# AI Text Summarizer — Intelligent Multi-Engine Platform

> A high-performance text summarization web platform featuring a dual-engine architecture: an ultra-fast, zero-dependency local extractive NLP engine and an AI abstractive summarizer powered by Google Gemini (`gemini-2.5-flash`). Built with a modern, responsive Single Page Application (SPA) interface.

---

## Key Features

### 1. Dual-Engine Summarization Core
* **Local Extractive NLP Engine:**
  * Runs 100% offline and privately on your machine without requiring an API key.
  * Powered by sublinear TF-IDF term salience, positional lead bias, and sentence graph ranking.
  * Instantaneous inference (typically < 30ms).
* **AI Abstractive Engine (Google Gemini):**
  * Powered by the `google-genai` SDK (`gemini-2.5-flash`).
  * Generates intelligent, natural language rewrites and contextual syntheses.
  * Configurable via local environment variable (`GEMINI_API_KEY`) or directly through the UI settings modal.
  * Automatic graceful fallback to the Local Engine if offline or if no API key is provided.

### 2. Formats & Granular Density Control
* **Three Output Modes:**
  * **Executive Paragraph:** Cohesive narrative summarizing core arguments and conclusions.
  * **Key Takeaways (Bullets):** Actionable, high-impact bullet points highlighting critical facts.
  * **TL;DR One-Liner:** Ultra-concise 1–2 sentence essence of the document.
* **Density Slider:** Adjust summary compression from Concise (20%) to Balanced (35%) or Comprehensive (55%).

### 3. Multi-Source Ingestion
* **Paste Raw Text:** Direct input with live word counter, character counter, and estimated reading time.
* **Web Article URL Scraper:** Enter any blog post, news article, or publication URL to automatically extract clean body text, removing ads, disclaimers, and navigation noise.
* **Document File Upload:** Drag-and-drop document upload supporting `.pdf`, `.txt`, and `.md` files up to 16MB.

### 4. Smart Reading Analytics & Productivity Tools
* **Real-Time Compression Metrics:**
  * Compression ratio percentage (e.g., `68% Reduced`).
  * Estimated reading time saved (e.g., `~3m 45s Saved`).
  * Before-and-after word count tracking.
* **Key Concept Extraction:** Automatic extraction of top thematic keywords and topic tags.
* **Action Toolbar:**
  * **One-Click Copy:** Copy summary directly to clipboard.
  * **Read Aloud (Audio):** Listen to synthesized speech via browser Web Speech API.
  * **Export:** Download summary as a Markdown (`.md`) or Plain Text (`.txt`) file.

### 5. UI Aesthetics & Theme
* Sleek, high-contrast dark theme (Obsidian + Electric Indigo & Cyan accents) and clean light theme.
* Ambient visual glow, glassmorphism cards, and responsive split-pane layout.

---

## Project Structure

```
Text_summariser/
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── .venv/                      # Virtual environment
└── Text_Summariser/
    ├── app.py                  # Flask application & REST API
    ├── summarizer.py           # Local NLP & Gemini summarization algorithms
    ├── scraper.py              # Web article scraper & PDF reader
    ├── templates/
    │   └── index.html          # Single Page Application template
    └── static/
        ├── css/
        │   └── style.css       # Design tokens & responsive styles
        └── js/
            └── app.js          # Interactive frontend controller
```

---

## Quick Start Guide

### Prerequisites
* Python 3.9+ installed on your system.

### 1. Set Up Virtual Environment & Dependencies
```bash
# Clone the repository
git clone https://github.com/official-urias/Text_summariser.git
cd Text_summariser

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# (Linux / macOS)
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. (Optional) Configure Gemini AI API Key
If you wish to use Google Gemini abstractive summarization, set your API key in an environment variable or create a `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(You can also input your API key directly inside the web UI via the Settings icon).*

### 3. Run the Application
```bash
# From within the project directory
python Text_Summariser/app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## API Endpoints

* `GET /`: Serves the Single Page Application.
* `GET /api/health`: Health status and Gemini engine readiness.
* `POST /api/summarize`: Main summarization endpoint. Accepts `{ text, engine, format, ratio, api_key }`.
* `POST /api/extract-url`: Scrapes clean article text from `{ url }`.
* `POST /api/upload`: Multipart file upload extracting text from `.txt`, `.md`, or `.pdf`.

---

## License
MIT License. Built by Urias.
