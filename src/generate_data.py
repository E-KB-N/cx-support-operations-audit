"""Generate a realistic synthetic Customer Experience support-ticket dataset.

Output:
    data/raw/cx_support_tickets.csv

Dependencies:
    pandas, numpy, faker
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker


SEED = 42
N_TICKETS = 2_500
N_CUSTOMERS = 1_650
LOOKBACK_DAYS = 90

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "cx_support_tickets.csv"

CATEGORIES = {
    "Billing/Refunds": [
        "Payment Failed",
        "Duplicate Charge",
        "Refund Pending",
        "Incorrect Amount",
    ],
    "App Bug": [
        "App Crash",
        "Login Timeout",
        "Page Not Loading",
        "Notification Error",
    ],
    "Account Access": [
        "Password Reset",
        "Account Locked",
        "Verification Code Missing",
        "Profile Update Failed",
    ],
    "Delivery Delay": [
        "Late Delivery",
        "Missing Items",
        "Tracking Not Updated",
        "Wrong Delivery Address",
    ],
    "Feature Request": [
        "Dark Mode",
        "Export Data",
        "New Payment Option",
        "Notification Controls",
    ],
}

CATEGORY_PROBABILITIES = [0.27, 0.24, 0.19, 0.18, 0.12]
CHANNELS = ["In-App Chat", "Email", "Social Media", "WhatsApp"]
CHANNEL_PROBABILITIES = [0.38, 0.29, 0.12, 0.21]
TIERS = ["Free", "Premium", "Enterprise"]
TIER_PROBABILITIES = [0.62, 0.28, 0.10]
STATUSES = ["Resolved", "Closed", "Escalated", "Open"]
STATUS_PROBABILITIES = [0.55, 0.25, 0.09, 0.11]

ISSUE_TEMPLATES = {
    "Payment Failed": "My payment keeps failing even though my details are correct.",
    "Duplicate Charge": "I was charged twice for the same transaction.",
    "Refund Pending": "My refund is still pending and I need an update.",
    "Incorrect Amount": "The amount on my bill does not match what I expected.",
    "App Crash": "The app closes every time I try to complete this action.",
    "Login Timeout": "I keep getting timed out when I try to sign in.",
    "Page Not Loading": "The page is stuck loading and I cannot continue.",
    "Notification Error": "The notifications are delayed or showing the wrong information.",
    "Password Reset": "I need help resetting my password.",
    "Account Locked": "My account is locked and I cannot get back in.",
    "Verification Code Missing": "The verification code has not arrived yet.",
    "Profile Update Failed": "I cannot save the changes to my profile.",
    "Late Delivery": "My order is later than the delivery estimate.",
    "Missing Items": "Some items were missing when my order arrived.",
    "Tracking Not Updated": "The tracking status has not changed for a while.",
    "Wrong Delivery Address": "The delivery address shown for my order is incorrect.",
    "Dark Mode": "I like the app and would find a dark mode option useful.",
    "Export Data": "Could you add a way to export my account data?",
    "New Payment Option": "It would be helpful to have another payment option.",
    "Notification Controls": "Please add more control over which notifications I receive.",
}

FOLLOW_UPS = {
    "negative": [
        "This has been very frustrating.",
        "Please resolve this as soon as possible.",
        "I have already tried again several times.",
        "This is disrupting what I need to do.",
    ],
    "neutral": [
        "Please let me know what information you need.",
        "Could someone advise me on the next step?",
        "I would appreciate an update when possible.",
        "Thank you for checking this for me.",
    ],
    "positive": [
        "The service has been useful overall, so this would be a great addition.",
        "Thanks for considering the suggestion.",
        "Everything else is working well for me.",
        "I would be happy to use this feature.",
    ],
}


def initialize_randomness() -> tuple[np.random.Generator, Faker]:
    """Initialize all random generators for reproducible output."""
    np.random.seed(SEED)
    Faker.seed(SEED)
    return np.random.default_rng(SEED), Faker("en_US")


def generate_created_timestamps(
    rng: np.random.Generator, n_rows: int, reference_time: pd.Timestamp
) -> pd.DatetimeIndex:
    """Create timestamps across the prior LOOKBACK_DAYS with recent-day weighting."""
    day_offsets = np.floor(rng.beta(1.25, 1.55, n_rows) * LOOKBACK_DAYS).astype(int)
    second_offsets = rng.integers(0, 86_400, n_rows)
    timestamps = reference_time - pd.to_timedelta(day_offsets, unit="D")
    timestamps -= pd.to_timedelta(second_offsets, unit="s")
    return pd.DatetimeIndex(timestamps).round("s")


def generate_response_times(
    rng: np.random.Generator, tiers: np.ndarray, channels: np.ndarray
) -> np.ndarray:
    """Generate right-skewed response times with SLA advantages by customer tier."""
    tier_medians = {"Free": 48.0, "Premium": 22.0, "Enterprise": 8.0}
    channel_factors = {
        "In-App Chat": 0.48,
        "WhatsApp": 0.70,
        "Social Media": 0.90,
        "Email": 1.55,
    }
    medians = np.array([tier_medians[t] for t in tiers])
    factors = np.array([channel_factors[c] for c in channels])
    noise = rng.lognormal(mean=0.0, sigma=0.62, size=len(tiers))
    return np.maximum(1, np.rint(medians * factors * noise)).astype(int)


def generate_resolution_times(
    rng: np.random.Generator,
    categories: np.ndarray,
    statuses: np.ndarray,
    tiers: np.ndarray,
) -> np.ndarray:
    """Generate category-dependent resolution hours; Open tickets remain null."""
    category_medians = {
        "Billing/Refunds": 31.0,
        "App Bug": 38.0,
        "Account Access": 10.0,
        "Delivery Delay": 23.0,
        "Feature Request": 15.0,
    }
    status_factors = {"Resolved": 0.82, "Closed": 1.00, "Escalated": 2.15, "Open": 1.0}
    tier_factors = {"Free": 1.12, "Premium": 0.92, "Enterprise": 0.76}

    base = np.array([category_medians[c] for c in categories])
    status_effect = np.array([status_factors[s] for s in statuses])
    tier_effect = np.array([tier_factors[t] for t in tiers])
    hours = base * status_effect * tier_effect * rng.lognormal(0, 0.58, len(categories))
    hours = np.clip(hours, 0.25, 240.0).round(2)
    hours[statuses == "Open"] = np.nan
    return hours


def generate_csat_scores(
    rng: np.random.Generator,
    categories: np.ndarray,
    statuses: np.ndarray,
    resolution_hours: np.ndarray,
) -> pd.array:
    """Generate CSAT with category penalties and a negative resolution-time effect."""
    category_effect = {
        "Billing/Refunds": -1.15,
        "App Bug": -1.30,
        "Account Access": -0.20,
        "Delivery Delay": -0.60,
        "Feature Request": 0.35,
    }
    score = 4.45 + np.array([category_effect[c] for c in categories])
    effective_hours = np.nan_to_num(resolution_hours, nan=72.0)
    score -= 0.62 * np.log1p(effective_hours / 12.0)
    score -= np.where(statuses == "Escalated", 0.55, 0.0)
    score -= np.where(statuses == "Open", 0.35, 0.0)
    score += rng.normal(0, 0.60, len(categories))
    scores = np.clip(np.rint(score), 1, 5)

    # Approximately 30% of all customers do not submit the post-support survey.
    survey_missing = rng.random(len(categories)) < 0.30
    scores[survey_missing] = np.nan
    return pd.array(scores, dtype="Int64")


def generate_ticket_text(
    rng: np.random.Generator, fake: Faker, category: str, subcategory: str
) -> str:
    """Build a short issue message with sentiment aligned to the ticket category."""
    if category in {"Billing/Refunds", "App Bug", "Delivery Delay"}:
        sentiment = "negative"
    elif category == "Feature Request":
        sentiment = "positive"
    else:
        sentiment = "neutral"

    message = ISSUE_TEMPLATES[subcategory]
    if rng.random() < 0.76:
        message = f"{message} {fake.random_element(FOLLOW_UPS[sentiment])}"
    return message


def build_dataset(n_tickets: int = N_TICKETS) -> pd.DataFrame:
    """Build the complete synthetic ticket dataset."""
    rng, fake = initialize_randomness()
    reference_time = pd.Timestamp.now(tz="UTC").floor("D").tz_localize(None)

    customer_pool = np.array([f"CUS-{i:06d}" for i in range(1, N_CUSTOMERS + 1)])
    # A mild Pareto weighting creates realistic repeat-contact customers.
    customer_weights = rng.pareto(2.8, N_CUSTOMERS) + 0.25
    customer_weights /= customer_weights.sum()

    categories = rng.choice(list(CATEGORIES), n_tickets, p=CATEGORY_PROBABILITIES)
    subcategories = np.array([fake.random_element(CATEGORIES[c]) for c in categories])
    channels = rng.choice(CHANNELS, n_tickets, p=CHANNEL_PROBABILITIES)
    tiers = rng.choice(TIERS, n_tickets, p=TIER_PROBABILITIES)
    statuses = rng.choice(STATUSES, n_tickets, p=STATUS_PROBABILITIES)
    created_at = generate_created_timestamps(rng, n_tickets, reference_time)
    response_minutes = generate_response_times(rng, tiers, channels)
    resolution_hours = generate_resolution_times(rng, categories, statuses, tiers)

    # A completed ticket cannot resolve after the dataset reference time.
    available_hours = (
        (reference_time - created_at).total_seconds().to_numpy() / 3_600
    )
    completed = statuses != "Open"
    resolution_hours[completed] = np.minimum(
        resolution_hours[completed], np.maximum(0.01, available_hours[completed])
    ).round(2)
    resolved_at = pd.Series(created_at + pd.to_timedelta(resolution_hours, unit="h"))
    resolved_at = resolved_at.clip(upper=reference_time)
    resolution_hours[completed] = (
        (resolved_at[completed].to_numpy() - created_at[completed].to_numpy())
        / np.timedelta64(1, "h")
    ).round(2)
    resolved_at[statuses == "Open"] = pd.NaT
    csat = generate_csat_scores(rng, categories, statuses, resolution_hours)

    ticket_text = [
        generate_ticket_text(rng, fake, category, subcategory)
        for category, subcategory in zip(categories, subcategories)
    ]

    return pd.DataFrame(
        {
            "ticket_id": [f"TKT-{10001 + i}" for i in range(n_tickets)],
            "customer_id": rng.choice(
                customer_pool, n_tickets, replace=True, p=customer_weights
            ),
            "created_at": created_at,
            "resolved_at": resolved_at,
            "channel": channels,
            "category": categories,
            "subcategory": subcategories,
            "customer_tier": tiers,
            "first_response_time_mins": response_minutes,
            "resolution_time_hours": resolution_hours,
            "csat_score": csat,
            "ticket_status": statuses,
            "ticket_text": ticket_text,
        }
    )


def validate_dataset(df: pd.DataFrame) -> None:
    """Fail fast if the generated output violates core business constraints."""
    expected_columns = [
        "ticket_id",
        "customer_id",
        "created_at",
        "resolved_at",
        "channel",
        "category",
        "subcategory",
        "customer_tier",
        "first_response_time_mins",
        "resolution_time_hours",
        "csat_score",
        "ticket_status",
        "ticket_text",
    ]
    assert list(df.columns) == expected_columns
    assert df["ticket_id"].is_unique
    assert df["csat_score"].dropna().between(1, 5).all()
    assert df.loc[df["ticket_status"] == "Open", "resolved_at"].isna().all()
    assert df.loc[df["ticket_status"] == "Open", "resolution_time_hours"].isna().all()
    assert df.loc[df["ticket_status"] != "Open", "resolved_at"].notna().all()
    assert (
        df.loc[df["ticket_status"] != "Open", "resolved_at"]
        >= df.loc[df["ticket_status"] != "Open", "created_at"]
    ).all()


def main() -> None:
    """Generate, validate, and persist the dataset."""
    dataset = build_dataset()
    validate_dataset(dataset)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(OUTPUT_PATH, index=False, date_format="%Y-%m-%d %H:%M:%S")
    print(f"Generated {len(dataset):,} rows at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()