SYSTEM_CATEGORY_LABELS: dict[str, dict[str, str]] = {
    "salary": {"ro": "Salariu", "en": "Salary"},
    "freelance": {"ro": "Freelance", "en": "Freelance"},
    "investments": {"ro": "Investiții", "en": "Investments"},
    "other_income": {"ro": "Alte venituri", "en": "Other income"},
    "rent": {"ro": "Chirie", "en": "Rent"},
    "food": {"ro": "Mâncare", "en": "Food"},
    "transport": {"ro": "Transport", "en": "Transport"},
    "utilities": {"ro": "Utilități", "en": "Utilities"},
    "shopping": {"ro": "Shopping", "en": "Shopping"},
    "health": {"ro": "Sănătate", "en": "Health"},
    "entertainment": {"ro": "Divertisment", "en": "Entertainment"},
    "other": {"ro": "Altele", "en": "Other"},
}


def display_category_name(name: str, slug: str | None, locale: str) -> str:
    if slug and locale in ("ro", "en"):
        labels = SYSTEM_CATEGORY_LABELS.get(slug)
        if labels:
            return labels[locale]
    return name
