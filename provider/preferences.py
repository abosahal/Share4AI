"""Presentation preferences are separate from sharing and runtime settings."""
import json
from .provision import atomic_json


def load_language(root):
    try:
        value = json.loads((root / 'preferences.json').read_text(encoding='utf-8'))['language']
        return value if value in ('ar', 'en') else 'ar'
    except (OSError, ValueError, KeyError, TypeError):
        return 'ar'


def save_language(root, language):
    if language not in ('ar', 'en'):
        raise ValueError('Unsupported language')
    atomic_json(root / 'preferences.json', {'language': language})
