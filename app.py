from flask import Flask, request, jsonify, render_template
import joblib
from newspaper import Article
import numpy as np
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
import tldextract
import feedparser
from langdetect import detect
from googletrans import Translator
from sentence_transformers import SentenceTransformer, util
from aiocache import cached
import time

app = Flask(__name__)

# =========================
# LOAD ML MODEL
# =========================
model = joblib.load("model/fake_news_model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")

# =========================
# TRANSLATOR SETUP
# =========================
translator = Translator()

def translate_to_english(text):
    try:
        # translator.detect/translate is synchronous, keeping it for now but wrapping in try
        detected = translator.detect(text)
        if detected.lang != "en":
            translated = translator.translate(text, dest="en")
            return translated.text
        else:
            return text
    except:
        return text

# =========================
# LOAD BERT MODEL
# =========================
bert_model = SentenceTransformer("all-MiniLM-L6-v2")

fake_reference = [
    "government hiding miracle cure",
    "celebrity secret conspiracy revealed",
    "viral whatsapp message about free money",
    "secret medicine cure discovered overnight"
]

fake_embeddings = bert_model.encode(fake_reference, convert_to_tensor=True)

# =========================
# TRUSTED RSS FEEDS
# =========================
trusted_rss = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://www.reuters.com/rssFeed/topNews",
    "https://www.ndtv.com/rss",
    "http://rss.cnn.com/rss/edition.rss"
]

# =========================
# TEXT NORMALIZATION
# =========================
def normalize_text(text):
    text = str(text)
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# =========================
# KEYWORD DETECTION
# =========================
fake_keywords = ["miracle cure", "secret government", "viral message", "click here", "shocking truth", "they dont want you to know", "100% guaranteed cure", "hidden truth"]

def keyword_score(text):
    score = 0
    for k in fake_keywords:
        if k in text:
            score += 1
    return score

# =========================
# SOURCE CREDIBILITY
# =========================
trusted_sources = ["bbc", "reuters", "cnn", "theguardian", "nytimes", "hindustantimes", "ndtv", "indiatoday", "timesofindia"]

def source_score(url):
    if not url: return 0
    domain = tldextract.extract(url).domain
    return -1 if domain in trusted_sources else 1

# =========================
# BERT SEMANTIC CHECK (Sync)
# =========================
def bert_score(text):
    embedding = bert_model.encode(text, convert_to_tensor=True)
    similarity = util.cos_sim(embedding, fake_embeddings)
    return similarity.max().item()

# =========================
# ASYNC GOOGLE NEWS CHECK
# =========================
@cached(ttl=600)
async def verify_with_google_news(text):
    query = text[:80]
    try:
        url = f"https://news.google.com/search?q={query}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                return len(soup.find_all("article")) > 3
    except:
        return False

# =========================
# ASYNC RSS NEWS VERIFICATION
# =========================
@cached(ttl=600)
async def verify_with_rss(text):
    query = " ".join(text.split()[:6])[:40]
    for rss_url in trusted_rss:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(rss_url, timeout=5) as response:
                    xml = await response.text()
                    feed = feedparser.parse(xml)
                    for entry in feed.entries[:10]:
                        if query in entry.title.lower():
                            return True
        except:
            continue
    return False

# =========================
# ASYNC EXTRACT ARTICLE TEXT
# =========================
async def extract_text(url):
    # Try newspaper first (Sync, but we wrap in thread if needed. For now, try fallback)
    try:
        article = Article(url)
        article.download()
        article.parse()
        if article.text.strip():
            return article.text[:5000]
    except:
        pass
    
    # Async Fallback
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                return " ".join([p.get_text() for p in soup.find_all("p")])[:5000]
    except:
        return ""

# =========================
# HYBRID AI ENGINE (Partial Async)
# =========================
async def hybrid_predict(text, url=""):
    # 1. ML and BERT (CPU intensive - Sync)
    vector = vectorizer.transform([text])
    ml_pred = model.predict(vector)[0]
    ml_conf = model.predict_proba(vector).max()
    bert_sim = bert_score(text)
    
    # 2. Async Network Tasks
    google_task = asyncio.create_task(verify_with_google_news(text))
    rss_task = asyncio.create_task(verify_with_rss(text))
    
    google_verified, rss_verified = await asyncio.gather(google_task, rss_task)
    
    # 3. Scores
    key_score = keyword_score(text)
    src_score = source_score(url)
    google_score = -1 if google_verified else 1
    rss_score = -1 if rss_verified else 1
    
    final_score = ml_pred + key_score + src_score + bert_sim + google_score + rss_score
    result = "Real News ✅" if final_score > 2 else "Fake News ❌"
    confidence = round((ml_conf + bert_sim) / 2 * 100, 2)
    
    return result, confidence

# =========================
# API ROUTES (Async)
# =========================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return {"status": "running", "version": "6.0 (Async Optimized)"}

@app.route("/predict", methods=["POST"])
async def predict():
    data = request.json
    text = data.get("text", "").strip()
    if not text: return jsonify({"prediction": "⚠ Please enter news text"})

    # Translation (Sync)
    text_en = translate_to_english(text)
    norm_text = normalize_text(text_en)

    result, confidence = await hybrid_predict(norm_text)
    
    return jsonify({
        "prediction": result,
        "confidence": f"{confidence}%",
        "explanation": ["AI Semantic Match", "Source Verification", "Network Integrity"]
    })

@app.route("/predict_url", methods=["POST"])
async def predict_url():
    data = request.json
    url = data.get("url", "").strip()
    if not url: return jsonify({"prediction": "⚠ Please enter URL"})

    text = await extract_text(url)
    if not text: return jsonify({"prediction": "⚠ Could not extract article text"})

    text_en = translate_to_english(text)
    norm_text = normalize_text(text_en)

    result, confidence = await hybrid_predict(norm_text, url)
    
    return jsonify({
        "prediction": result,
        "confidence": f"{confidence}%",
        "explanation": ["URL Credibility", "Cross-Reference Check", "BERT Semantic Context"]
    })

if __name__ == "__main__":
    app.run(debug=False) # Production mode
