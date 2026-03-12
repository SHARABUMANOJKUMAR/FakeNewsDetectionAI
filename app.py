from flask import Flask, request, jsonify, render_template
import joblib
from newspaper import Article
import numpy as np
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Load ML model
model = joblib.load("model/fake_news_model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")


# ================================
# Extract article text from URL
# ================================
def extract_text(url):

    # First attempt: newspaper3k
    try:
        article = Article(url)
        article.download()
        article.parse()

        if article.text.strip():
            return article.text[:5000]

    except:
        pass

    # Fallback method using BeautifulSoup
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")

        text = " ".join([p.get_text() for p in paragraphs])

        return text[:5000]

    except:
        return ""


# ================================
# Explain prediction (top keywords)
# ================================
def explain_prediction(text):

    vector = vectorizer.transform([text])

    feature_names = np.array(vectorizer.get_feature_names_out())

    vector_array = vector.toarray()[0]

    top_indices = vector_array.argsort()[-5:][::-1]

    important_words = feature_names[top_indices]

    return important_words.tolist()


# ================================
# Home Page
# ================================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return {"status": "running"}

# ================================
# TEXT CHECK
# ================================
@app.route("/predict", methods=["POST"])
def predict():

    data = request.json
    text = data.get("text", "")

    if text.strip() == "":
        return jsonify({"prediction": "⚠ Please enter news text"})

    vector = vectorizer.transform([text])

    prediction = model.predict(vector)[0]

    # Confidence score
    confidence = round(model.predict_proba(vector).max() * 100, 2)

    explanation = explain_prediction(text)

    result = "Fake News ❌" if prediction == 0 else "Real News ✅"

    return jsonify({
        "prediction": result,
        "confidence": f"{confidence}%",
        "explanation": explanation
    })


# ================================
# URL CHECK
# ================================
@app.route("/predict_url", methods=["POST"])
def predict_url():

    data = request.json
    url = data.get("url", "")

    if url.strip() == "":
        return jsonify({
            "prediction": "⚠ Please enter URL",
            "explanation": []
        })

    article_text = extract_text(url)

    if article_text == "":
        return jsonify({
            "prediction": "⚠ Could not extract article text",
            "explanation": ["Try using a full article link instead of a homepage"]
        })

    vector = vectorizer.transform([article_text])

    prediction = model.predict(vector)[0]

    # Confidence score
    confidence = round(model.predict_proba(vector).max() * 100, 2)

    explanation = explain_prediction(article_text)

    result = "Fake News ❌" if prediction == 0 else "Real News ✅"

    return jsonify({
        "prediction": result,
        "confidence": f"{confidence}%",
        "explanation": explanation
    })


if __name__ == "__main__":
    app.run(debug=True)