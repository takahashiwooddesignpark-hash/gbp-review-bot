import json
import os
from typing import Set

STORAGE_FILE = os.path.join(os.path.dirname(__file__), "seen_reviews.json")


def load_seen_ids() -> Set[str]:
    if not os.path.exists(STORAGE_FILE):
        return set()
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("seen_ids", []))


def save_seen_ids(ids: Set[str]) -> None:
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen_ids": list(ids)}, f, ensure_ascii=False, indent=2)
