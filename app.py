from flask import Flask, request, jsonify, render_template
import joblib
from newspaper import Article
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
import tldextract
import feedparser

from langdetect import detect
from googletrans import Translator

from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# =========================
# LOAD ML MODEL
# =========================
model = joblib.load("model/fake_news_model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")

translator = Translator()

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

    try:
        lang = detect(text)
    except:
        lang = "en"

    if lang != "en":
        try:
            text = translator.translate(text, dest="en").text
        except:
            pass

    text = text.lower()

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# =========================
# KEYWORD DETECTION
# =========================
fake_keywords = [
    "miracle cure",
    "secret government",
    "viral message",
    "click here",
    "shocking truth",
    "they dont want you to know",
    "100% guaranteed cure",
    "hidden truth"
]

def keyword_score(text):

    score = 0

    for k in fake_keywords:
        if k in text:
            score += 1

    return score


# =========================
# SOURCE CREDIBILITY
# =========================
trusted_sources = [
    "bbc","reuters","cnn","theguardian","nytimes",
    "hindustantimes","ndtv","indiatoday","timesofindia"
]

def source_score(url):

    if url == "":
        return 0

    domain = tldextract.extract(url).domain

    if domain in trusted_sources:
        return -1

    return 1


# =========================
# BERT SEMANTIC CHECK
# =========================
def bert_score(text):

    embedding = bert_model.encode(text, convert_to_tensor=True)

    similarity = util.cos_sim(embedding, fake_embeddings)

    max_score = similarity.max().item()

    return max_score


# =========================
# GOOGLE NEWS CHECK
# =========================
def verify_with_google_news(text):

    query = text[:80]

    try:

        url = f"https://news.google.com/search?q={query}"

        r = requests.get(url, timeout=5)

        soup = BeautifulSoup(r.text, "html.parser")

        articles = soup.find_all("article")

        if len(articles) > 3:
            return True

    except:
        pass

    return False


# =========================
# RSS NEWS VERIFICATION
# =========================
def verify_with_rss(text):

    query = " ".join(text.split()[:6])

    for rss_url in trusted_rss:

        try:

            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:10]:

                title = entry.title.lower()

                if query[:40] in title:
                    return True

        except:
            pass

    return False


# =========================
# EXTRACT ARTICLE TEXT
# =========================
def extract_text(url):

    try:

        article = Article(url)

        article.download()

        article.parse()

        if article.text.strip():
            return article.text[:5000]

    except:
        pass

    try:

        response = requests.get(url, timeout=10)

        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")

        text = " ".join([p.get_text() for p in paragraphs])

        return text[:5000]

    except:
        return ""


# =========================
# EXPLAIN MODEL
# =========================
def explain_prediction(text):

    vector = vectorizer.transform([text])

    feature_names = np.array(vectorizer.get_feature_names_out())

    vector_array = vector.toarray()[0]

    top_indices = vector_array.argsort()[-5:][::-1]

    important_words = feature_names[top_indices]

    return important_words.tolist()


# =========================
# HYBRID AI ENGINE
# =========================
def hybrid_predict(text, url=""):

    vector = vectorizer.transform([text])

    ml_pred = model.predict(vector)[0]

    ml_conf = model.predict_proba(vector).max()

    key_score = keyword_score(text)

    src_score = source_score(url)

    bert_sim = bert_score(text)

    google_verified = verify_with_google_news(text)

    rss_verified = verify_with_rss(text)

    google_score = -1 if google_verified else 1

    rss_score = -1 if rss_verified else 1

    final_score = ml_pred + key_score + src_score + bert_sim + google_score + rss_score

    if final_score > 2:
        result = "Real News ✅"
    else:
        result = "Fake News ❌"

    confidence = round((ml_conf + bert_sim) / 2 * 100, 2)

    return result, confidence


# =========================
# HOME PAGE
# =========================
@app.route("/")
def home():
    return render_template("index.html")


# =========================
# HEALTH API
# =========================
@app.route("/health")
def health():
    return {
        "status": "running",
        "service": "Hybrid Fake News Detection API",
        "version": "5.0"
    }


# =========================
# TEXT PREDICTION
# =========================
@app.route("/predict", methods=["POST"])
def predict():

    data = request.json

    text = data.get("text", "")

    if text.strip() == "":
        return jsonify({"prediction": "⚠ Please enter news text"})

    text = normalize_text(text)

    result, confidence = hybrid_predict(text)

    explanation = explain_prediction(text)

    return jsonify({
        "prediction": result,
        "confidence": f"{confidence}%",
        "explanation": explanation
    })


# =========================
# URL PREDICTION
# =========================
@app.route("/predict_url", methods=["POST"])
def predict_url():

    data = request.json

    url = data.get("url", "")

    if url.strip() == "":
        return jsonify({
            "prediction": "⚠ Please enter URL"
        })

    article_text = extract_text(url)

    if article_text == "":
        return jsonify({
            "prediction": "⚠ Could not extract article text"
        })

    article_text = normalize_text(article_text)

    result, confidence = hybrid_predict(article_text, url)

    explanation = explain_prediction(article_text)

    return jsonify({
        "prediction": result,
        "confidence": f"{confidence}%",
        "explanation": explanation
    })


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(debug=True)
    