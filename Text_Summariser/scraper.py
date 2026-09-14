"""
Content Ingestion Engine: Web Article Scraper & Multi-Format Document Reader
"""

import io
import re
from urllib.parse import urlparse

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def extract_from_url(url: str) -> dict:
    """
    Fetches and extracts clean article text and metadata from a web page URL.
    """
    import requests
    from bs4 import BeautifulSoup

    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid URL. Please include http:// or https://")

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
            allow_redirects=True
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise ConnectionError(f"Could not retrieve webpage: {str(e)}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find('h1'):
        title = soup.find('h1').get_text().strip()

    # Remove non-content elements
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg", "iframe"]):
        element.decompose()

    # Priority 1: Check for <article> or <main>
    container = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'(content|article|post|body|entry)', re.I))
    if not container:
        container = soup.body or soup

    # Extract paragraph texts
    paragraphs = container.find_all('p')
    meaningful_paras = []
    for p in paragraphs:
        text = p.get_text().strip()
        # Filter out short link bars or disclaimers
        if len(text.split()) >= 6:
            meaningful_paras.append(text)

    if meaningful_paras:
        extracted_text = "\n\n".join(meaningful_paras)
    else:
        # Fallback to general container text
        extracted_text = container.get_text(separator="\n", strip=True)
        # Collapse excessive newlines
        extracted_text = re.sub(r'\n{3,}', '\n\n', extracted_text)

    if not extracted_text or len(extracted_text.split()) < 15:
        raise ValueError("Could not find sufficient readable article text at this URL.")

    return {
        "title": title or parsed.netloc,
        "text": extracted_text,
        "url": url,
        "word_count": len(re.findall(r'\b\w+\b', extracted_text))
    }


def extract_from_file(file_storage) -> dict:
    """
    Extracts text content from uploaded file (.txt, .md, .pdf).
    """
    filename = getattr(file_storage, 'filename', '') or 'document.txt'
    ext = filename.lower().split('.')[-1] if '.' in filename else 'txt'

    if ext in ['txt', 'md', 'text']:
        raw_bytes = file_storage.read()
        try:
            text = raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            text = raw_bytes.decode('latin-1', errors='replace')
    elif ext == 'pdf':
        try:
            import pypdf
            pdf_bytes = io.BytesIO(file_storage.read())
            reader = pypdf.PdfReader(pdf_bytes)
            pages_text = []
            for idx, page in enumerate(reader.pages):
                page_content = page.extract_text() or ''
                if page_content.strip():
                    pages_text.append(page_content.strip())
            text = "\n\n".join(pages_text)
            if not text.strip():
                raise ValueError("The PDF contains no extractable text (it might be scanned images).")
        except Exception as e:
            raise ValueError(f"Failed to read PDF file: {str(e)}")
    else:
        raise ValueError(f"Unsupported file extension: .{ext}. Please upload a .txt, .md, or .pdf file.")

    text = text.strip()
    if not text:
        raise ValueError("Uploaded file is empty.")

    return {
        "filename": filename,
        "text": text,
        "word_count": len(re.findall(r'\b\w+\b', text))
    }
