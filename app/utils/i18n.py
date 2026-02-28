"""
Internationalization and localization settings
"""

import json
import os
from pathlib import Path

CURRENCIES = {
    "EUR": "€",
    "GBP": "£",
    "USD": "$",
    "RSD": "дин",
    "BAM": "KM",
    "PLN": "zł",
    "HUF": "Ft",
    "CZK": "Kč",
    "HRK": "kn",
    "BGN": "лв",
    "RON": "lei",
    "SKK": "Sk",
}

LANGUAGES = {
    "sr": "Srpski",
    "en": "English",
}

# Try to load translations from JSON file
def load_translations():
    """Load translations from JSON file, fallback to empty dict if not found"""
    try:
        # Try multiple paths for the translations.json file
        possible_paths = [
            # Path relative to this file (app/utils/i18n.py)
            Path(__file__).parent.parent.parent / "frontend" / "static" / "translations.json",
            # Absolute path if running from project root
            Path("frontend/static/translations.json"),
            # Path if running from app directory
            Path("../frontend/static/translations.json"),
        ]
        
        for json_path in possible_paths:
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                    print(f"Loaded translations from: {json_path}")
                    return translations
        
        print("Warning: translations.json not found, using empty translations")
    except Exception as e:
        print(f"Error loading translations from JSON: {e}")
    
    # Return minimal translations if file not found
    return {
        "sr": {},
        "en": {},
    }

TRANSLATIONS = load_translations()


def get_translation(language: str, key: str) -> str:
    """Get translated string by language and key"""
    if language not in TRANSLATIONS:
        language = "sr"
    
    translations = TRANSLATIONS.get(language, {})
    return translations.get(key, key)


def get_currency_symbol(currency: str) -> str:
    """Get currency symbol"""
    return CURRENCIES.get(currency, currency)

