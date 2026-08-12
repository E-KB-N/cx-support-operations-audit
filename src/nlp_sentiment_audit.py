"""Enrich CX support tickets with sentiment and root-cause phrase analysis.

Inputs:
    data/raw/cx_support_tickets.csv

Outputs:
    data/processed/cx_tickets_enriched.csv
    data/processed/nlp_summary.json

Dependencies:
    pandas, nltk
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "cx_support_tickets.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
ENRICHED_PATH = OUTPUT_DIR / "cx_tickets_enriched.csv"
SUMMARY_PATH = OUTPUT_DIR / "nlp_summary.json"
NLTK_DATA_PATH = PROJECT_ROOT / ".nltk_data"

TEXT_COLUMN = "ticket_text"
CSAT_COLUMN = "csat_score"
TOKEN_PATTERN = re.compile(r"[a-z]+(?:'[a-z]+)?")
REQUIRED_NLTK_RESOURCES = {
    "vader_lexicon": "sentiment/vader_lexicon.zip",
    "stopwords": "corpora/stopwords",
}


def ensure_nltk_resources() -> None:
    """Download required NLTK data only when it is not already available."""
    NLTK_DATA_PATH.mkdir(parents=True, exist_ok=True)
    nltk_data_directory = str(NLTK_DATA_PATH)
    if nltk_data_directory not in nltk.data.path:
        nltk.data.path.insert(0, nltk_data_directory)

    for package, resource_path in REQUIRED_NLTK_RESOURCES.items():
        try:
            nltk.data.find(resource_path)
        except LookupError:
            try:
                downloaded = nltk.download(
                    package, download_dir=NLTK_DATA_PATH, quiet=True
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Unable to download the NLTK resource '{package}'. "
                    "Check the network connection and retry."
                ) from exc
            if not downloaded:
                raise RuntimeError(f"NLTK could not download '{package}'.")


def load_tickets(path: Path = INPUT_PATH) -> pd.DataFrame:
    """Load input data and validate fields required by this audit."""
    if not path.exists():
        raise FileNotFoundError(f"Input dataset not found: {path}")

    tickets = pd.read_csv(path)
    missing_columns = {TEXT_COLUMN, CSAT_COLUMN}.difference(tickets.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Input dataset is missing required columns: {missing}")

    # Preserve rows with missing text while making them safe for NLP scoring.
    tickets[TEXT_COLUMN] = tickets[TEXT_COLUMN].fillna("").astype(str)
    tickets[CSAT_COLUMN] = pd.to_numeric(tickets[CSAT_COLUMN], errors="coerce")
    return tickets


def categorize_sentiment(score: float) -> str:
    """Map a VADER compound score to the standard three sentiment bands."""
    if score >= 0.05:
        return "Positive"
    if score <= -0.05:
        return "Negative"
    return "Neutral"


def add_sentiment_columns(
    tickets: pd.DataFrame, analyzer: SentimentIntensityAnalyzer
) -> pd.DataFrame:
    """Return a copy of the tickets with VADER score and category fields."""
    enriched = tickets.copy()
    enriched["sentiment_score"] = enriched[TEXT_COLUMN].map(
        lambda text: analyzer.polarity_scores(text)["compound"]
    )
    enriched["sentiment_score"] = enriched["sentiment_score"].round(4)
    enriched["sentiment_category"] = enriched["sentiment_score"].map(
        categorize_sentiment
    )
    return enriched


def extract_top_negative_bigrams(
    tickets: pd.DataFrame, stop_words: set[str], limit: int = 10
) -> list[dict[str, Any]]:
    """Count meaningful bigrams among negative-sentiment or low-CSAT tickets."""
    root_cause_mask = (tickets["sentiment_category"] == "Negative") | (
        tickets[CSAT_COLUMN].le(2).fillna(False)
    )

    bigram_counts: Counter[tuple[str, str]] = Counter()
    for text in tickets.loc[root_cause_mask, TEXT_COLUMN]:
        tokens = [
            token
            for token in TOKEN_PATTERN.findall(text.lower())
            if token not in stop_words and len(token) > 1
        ]
        bigram_counts.update(zip(tokens, tokens[1:]))

    return [
        {"phrase": " ".join(phrase), "count": int(count)}
        for phrase, count in bigram_counts.most_common(limit)
    ]


def build_summary(
    tickets: pd.DataFrame, top_phrases: list[dict[str, Any]]
) -> dict[str, Any]:
    """Create a serializable NLP audit summary with counts and percentages."""
    total_tickets = len(tickets)
    category_order = ["Positive", "Neutral", "Negative"]
    counts = tickets["sentiment_category"].value_counts()
    average_csat = tickets.groupby("sentiment_category")[CSAT_COLUMN].mean()

    distribution = {
        category: {
            "count": int(counts.get(category, 0)),
            "percentage": round(
                100.0 * int(counts.get(category, 0)) / total_tickets, 2
            )
            if total_tickets
            else 0.0,
        }
        for category in category_order
    }
    csat_by_sentiment = {
        category: (
            round(float(average_csat[category]), 2)
            if category in average_csat.index
            and pd.notna(average_csat[category])
            else None
        )
        for category in category_order
    }

    return {
        "total_tickets": total_tickets,
        "sentiment_distribution": distribution,
        "average_csat_by_sentiment": csat_by_sentiment,
        "top_negative_key_phrases": top_phrases,
    }


def run_audit() -> dict[str, Any]:
    """Execute the complete NLP enrichment and reporting pipeline."""
    ensure_nltk_resources()
    tickets = load_tickets()
    analyzer = SentimentIntensityAnalyzer()
    enriched = add_sentiment_columns(tickets, analyzer)

    english_stop_words = set(stopwords.words("english"))
    top_phrases = extract_top_negative_bigrams(enriched, english_stop_words)
    summary = build_summary(enriched, top_phrases)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(ENRICHED_PATH, index=False)
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    """Run the audit and print the same summary written to disk."""
    summary = run_audit()
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
