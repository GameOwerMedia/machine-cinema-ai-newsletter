from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Set

from filelock import FileLock

LOGGER = logging.getLogger(__name__)


@dataclass
class SeenCache:
    path: Path = Path(".cache/seen.json")
    scope: str = "rolling"  # rolling | daily
    ttl_days: int | None = None
    reset: bool = False

    def __post_init__(self) -> None:
        self.scope = self.scope or "rolling"
        if self.scope not in {"rolling", "daily"}:
            raise ValueError("seen scope must be 'rolling' or 'daily'")
        if self.reset and self.path.exists():
            self.path.unlink()
        self.data = {"rolling": {}, "daily": {}}
        self._load()
        self._prune()

    # ----------------- Persistence helpers -----------------
    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except json.JSONDecodeError:
            LOGGER.warning("Seen cache corrupted, resetting: %s", self.path)
            return
        if not isinstance(payload, dict):
            return
        rolling = payload.get("rolling") or {}
        if isinstance(rolling, dict):
            self.data["rolling"] = {str(k): str(v) for k, v in rolling.items()}
        daily = payload.get("daily") or {}
        if isinstance(daily, dict):
            self.data["daily"] = {
                str(day): [str(item) for item in items]
                for day, items in daily.items()
                if isinstance(items, list)
            }

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(self.data, fh, ensure_ascii=False, indent=2)

    # ----------------- Locking -----------------
    @contextmanager
    def acquire_lock(self, day: date) -> Iterator[None]:
        lock_dir = self.path.parent / "locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        lock_path = lock_dir / f"{day.isoformat()}.lock"
        lock = FileLock(lock_path)
        lock.acquire()
        try:
            yield
        finally:
            lock.release()

    # ----------------- TTL & pruning -----------------
    def _prune(self) -> None:
        if not self.ttl_days or self.ttl_days <= 0:
            return
        cutoff = datetime.now(UTC).date() - timedelta(days=self.ttl_days)
        if self.scope == "rolling":
            to_delete = [link for link, seen_day in self.data["rolling"].items() if _older_than(seen_day, cutoff)]
            for link in to_delete:
                self.data["rolling"].pop(link, None)
        else:
            for day in list(self.data["daily"].keys()):
                if _older_than(day, cutoff):
                    self.data["daily"].pop(day, None)
        self._save()

    # ----------------- Public API -----------------
    def filter_new(self, links: Iterable[str], day: date) -> List[str]:
        seen = self._seen_set(day)
        return [link for link in links if link not in seen]

    def _seen_set(self, day: date) -> Set[str]:
        if self.scope == "rolling":
            return set(self.data["rolling"].keys())
        return set(self.data["daily"].get(day.isoformat(), []))

    def remember(self, day: date, links: Iterable[str]) -> None:
        links_list = list(dict.fromkeys(link for link in links if link))
        if not links_list:
            return
        if self.scope == "rolling":
            for link in links_list:
                self.data["rolling"][link] = day.isoformat()
        else:
            bucket = self.data["daily"].setdefault(day.isoformat(), [])
            existing = set(bucket)
            for link in links_list:
                if link not in existing:
                    bucket.append(link)
        self._prune()
        self._save()


def _older_than(stored_day: str, cutoff: date) -> bool:
    try:
        parsed = datetime.fromisoformat(stored_day).date()
    except ValueError:
        try:
            parsed = datetime.strptime(stored_day, "%Y-%m-%d").date()
        except ValueError:
            return True
    return parsed < cutoff
