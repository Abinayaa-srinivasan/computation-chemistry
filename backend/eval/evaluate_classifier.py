"""Evaluate the ML category suggester (for your viva).

Method: leave-one-out cross-validation on the seeded ingredient table. For each ingredient we
train on all the OTHERS and predict its primary (first) category from its name alone.
Run from the backend folder:  python -m eval.evaluate_classifier
Needs scikit-learn. Prints overall accuracy and per-category precision / recall / F1.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.db import connect, DB_PATH
from app.analyzer import load_catalog


def main():
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import classification_report
        from sklearn.model_selection import LeaveOneOut, cross_val_predict
        from sklearn.pipeline import make_pipeline
    except ImportError:
        sys.exit("scikit-learn is required: pip install scikit-learn")
    cat = load_catalog(connect(os.environ.get("DERMALENS_DB", DB_PATH)))
    names = [i["norm_name"] for i in cat["ingredients"].values() if i["categories"]]
    labels = [i["categories"][0] for i in cat["ingredients"].values() if i["categories"]]
    model = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4)),
                          LogisticRegression(max_iter=3000, C=20))
    pred = cross_val_predict(model, names, labels, cv=LeaveOneOut())
    acc = sum(p == y for p, y in zip(pred, labels)) / len(labels)
    print(f"Ingredients: {len(labels)}   Leave-one-out accuracy: {acc:.1%}\n")
    print(classification_report(labels, pred, zero_division=0))
    print("Note: names alone are weak evidence for many categories (e.g. plant oils vs extracts), so the\n"
          "app shows the confidence and labels every ML result as a suggestion.")


if __name__ == "__main__":
    main()
