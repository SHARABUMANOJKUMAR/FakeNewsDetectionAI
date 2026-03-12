import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
import joblib

# Load datasets
fake = pd.read_csv("dataset/Fake.csv")
true = pd.read_csv("dataset/True.csv")

# Labels
fake["label"] = 0
true["label"] = 1

# Combine
data = pd.concat([fake, true])

# Shuffle
data = data.sample(frac=1).reset_index(drop=True)

# Features
X = data["text"]
y = data["label"]

# Vectorization
vectorizer = TfidfVectorizer(stop_words="english", max_df=0.7)

X_vector = vectorizer.fit_transform(X)

# Train test split
X_train, X_test, y_train, y_test = train_test_split(
    X_vector, y, test_size=0.2, random_state=42
)

# Model
model = MultinomialNB()

model.fit(X_train, y_train)

pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, pred))

# Save model
joblib.dump(model, "model/fake_news_model.pkl")
joblib.dump(vectorizer, "model/vectorizer.pkl")