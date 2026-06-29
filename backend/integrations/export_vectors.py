"""
Utilities for exporting vector-store metadata/context.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from database.chroma_manager import get_collection


def export_collection(collection_name: str, output_path: str | Path) -> dict[str, Any]:
    collection = get_collection(collection_name)
    payload = collection.get(include=["documents", "metadatas"])
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
    return {"collection_name": collection_name, "output_path": str(path), "count": len(payload.get("ids", []))}
