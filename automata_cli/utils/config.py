from pathlib import Path
import json
import yaml


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding='utf-8')
    if path.suffix.lower() in ('.yml', '.yaml'):
        return yaml.safe_load(text) or {}
    if path.suffix.lower() == '.json':
        return json.loads(text or '{}')
    return {}


