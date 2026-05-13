import json, os

DATA_DIR = "data"

def load(filename: str, default):
    """Load a JSON file from the data directory. Returns default if missing or corrupt."""
    path = os.path.join(DATA_DIR, filename)
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default

def save(filename: str, data):
    """Save data to a JSON file in the data directory."""
    path = os.path.join(DATA_DIR, filename)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_guild_settings():
    """Load guild settings from GuildSettings.json"""
    if not os.path.exists("GuildSettings.json"):
        return {}
    try:
        with open("GuildSettings.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_guild_settings(data):
    """Save guild settings to GuildSettings.json"""
    with open("GuildSettings.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
