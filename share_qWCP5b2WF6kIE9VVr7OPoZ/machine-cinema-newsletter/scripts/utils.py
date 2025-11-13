"""Utility functions for the newsletter system."""
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def read_json(path: Path) -> Any:
    """Read JSON file."""
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(path: Path, data: Any) -> None:
    """Write JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_dirs(*paths: Path) -> None:
    """Ensure directories exist."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)

def today_pl_date() -> str:
    """Get today's date in Poland timezone (YYYY-MM-DD format)."""
    # For simplicity, using UTC+1 (Europe/Warsaw standard time)
    # In production, use zoneinfo for proper timezone handling
    from datetime import timedelta
    now = datetime.now(timezone.utc) + timedelta(hours=1)
    return now.strftime("%Y-%m-%d")

def now_pl() -> datetime:
    """Get current datetime in Poland timezone."""
    from datetime import timedelta
    return datetime.now(timezone.utc) + timedelta(hours=1)

def canonical_or_allowed(url: str) -> str:
    """Return canonical URL or original if allowed."""
    # Simplified version - in production, implement proper URL canonicalization
    return url.strip()

def idempotent_guard_for_today(site_dir: Path, date_str: str) -> bool:
    """Check if today's newsletter already exists."""
    import os
    daily_html = site_dir / f"{date_str}.html"
    if daily_html.exists() and os.environ.get("FORCE_RUN", "0") != "1":
        return True
    return False
