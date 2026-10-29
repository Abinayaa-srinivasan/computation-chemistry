"""Ingredient-name normalisation shared by the seed loader and (later) the analyzer."""
import re
import unicodedata


def normalize(name: str) -> str:
    """lowercase, strip accents, remove punctuation noise, collapse whitespace.

    'Aqua / Water ' -> 'aqua water'; 'Sodium  Hyaluronate.' -> 'sodium hyaluronate'
    """
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ")
    s = re.sub(r"\(.*?\)", " ", s)       # drop parenthetical notes like (nano)
    s = re.sub(r"[^a-z0-9/+\- ]", " ", s)  # keep letters, digits and a few INCI symbols
    s = re.sub(r"\s+", " ", s).strip()
    return s


def split_ingredient_list(text: str):
    """Split a pasted or OCR-read label into individual ingredient names (label order).

    Labels wrap lines in the middle of a name, so when commas are present we treat line breaks as
    spaces (and rejoin words hyphenated at a line end); with no commas, each line is one ingredient.
    """
    text = (text or "").strip()
    text = re.sub(r"(?i)^\s*(ingredients?|inci|contains)\s*[:\-]?\s*", "", text)
    if "," in text or ";" in text:
        text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
        text = re.sub(r"\s*\n\s*", " ", text)
        parts = re.split(r"[,;\u2022\u00b7]+", text)
    else:
        parts = re.split(r"[\n\u2022\u00b7]+", text)
    return [p.strip(" .\t") for p in parts if p.strip(" .\t")]
