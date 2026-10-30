DOMAIN = "waste_collection"
STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 1

SIGNAL_SCHEDULE_UPDATED = f"{DOMAIN}_schedule_updated"

WASTE_TYPES = ["bio", "mixed", "plastic", "paper", "glass"]

WASTE_LABELS = {
    "en": {
        "bio": "Bio",
        "mixed": "Mixed",
        "plastic": "Plastic",
        "paper": "Paper",
        "glass": "Glass",
    },
    "pl": {
        "bio": "Bio",
        "mixed": "Zmieszane",
        "plastic": "Plastik",
        "paper": "Papier",
        "glass": "Szkło",
    },
}

WASTE_ICONS = {
    "bio": "mdi:leaf",
    "mixed": "mdi:trash-can-outline",
    "plastic": "mdi:bottle-soda-classic-outline",
    "paper": "mdi:newspaper-variant-outline",
    "glass": "mdi:glass-fragile",
}


def waste_label(language: str | None, waste_type: str) -> str:
    """Return a localized label for a waste type (falls back to English)."""
    lang = (language or "en").split("-")[0].lower()
    labels = WASTE_LABELS.get(lang, WASTE_LABELS["en"])
    return labels.get(waste_type, waste_type)
