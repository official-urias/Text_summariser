"""
Comprehensive Verification Test Suite for Rebuilt Text Summarizer
"""

import sys
import unittest
from pathlib import Path

# Add directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from summarizer import summarize_local, extract_keywords, calculate_metrics
    from scraper import extract_from_url
    from app import app as flask_app
except ImportError:
    from Text_Summariser.summarizer import summarize_local, extract_keywords, calculate_metrics
    from Text_Summariser.scraper import extract_from_url
    from Text_Summariser.app import app as flask_app



SAMPLE_TEXT = (
    "Artificial intelligence is rapidly transforming global industry and research. "
    "Machine learning models are now capable of analyzing massive datasets in fractions of a second. "
    "However, data privacy and algorithmic transparency remain significant challenges for modern engineers. "
    "Federated learning has emerged as a compelling solution to train neural networks across decentralized nodes. "
    "By combining homomorphic encryption with distributed aggregation, institutions can ensure zero gradient leakage. "
    "Ultimately, the goal of modern AI engineering is building robust, high-performance systems that serve humanity ethically."
)


class TestSummarizerCore(unittest.TestCase):

    def test_local_paragraph_summary(self):
        result = summarize_local(SAMPLE_TEXT, ratio=0.4, output_format="paragraph")
        self.assertIn("summary", result)
        self.assertGreater(len(result["summary"]), 20)
        self.assertEqual(result["format"], "paragraph")
        self.assertEqual(result["engine"], "local-extractive")

    def test_local_bullets_summary(self):
        result = summarize_local(SAMPLE_TEXT, ratio=0.4, output_format="bullets")
        self.assertIn("•", result["summary"])
        self.assertEqual(result["format"], "bullets")

    def test_local_tldr_summary(self):
        result = summarize_local(SAMPLE_TEXT, output_format="tldr")
        self.assertIn("summary", result)
        self.assertEqual(result["format"], "tldr")
        # Should be a single concise sentence
        self.assertNotIn("\n", result["summary"].strip())

    def test_keyword_extraction(self):
        keywords = extract_keywords(SAMPLE_TEXT, top_n=5)
        self.assertIsInstance(keywords, list)
        self.assertGreaterEqual(len(keywords), 3)

    def test_metrics_calculation(self):
        result = summarize_local(SAMPLE_TEXT, ratio=0.35, output_format="paragraph")
        metrics = calculate_metrics(SAMPLE_TEXT, result["summary"])
        self.assertIn("compression_percent", metrics)
        self.assertIn("time_saved_display", metrics)
        self.assertGreater(metrics["original_words"], metrics["summary_words"])
        self.assertGreaterEqual(metrics["compression_percent"], 0)


class TestFlaskAPI(unittest.TestCase):

    def setUp(self):
        flask_app.testing = True
        self.client = flask_app.test_client()

    def test_get_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AI Text Summarizer", response.data)
        self.assertIn(b"Text Summarizer", response.data)

    def test_api_health(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "online")

    def test_api_summarize_success(self):
        payload = {
            "text": SAMPLE_TEXT,
            "engine": "local",
            "format": "paragraph",
            "ratio": 0.4
        }
        response = self.client.post('/api/summarize', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("summary", data)
        self.assertIn("metrics", data)
        self.assertIn("keywords", data)
        self.assertEqual(data["engine"], "local-extractive")

    def test_api_summarize_empty(self):
        response = self.client.post('/api/summarize', json={"text": ""})
        self.assertEqual(response.status_code, 400)

    def test_api_summarize_too_short(self):
        response = self.client.post('/api/summarize', json={"text": "Just three words."})
        self.assertEqual(response.status_code, 400)

    def test_api_extract_url_invalid(self):
        response = self.client.post('/api/extract-url', json={"url": "not-a-valid-url"})
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
