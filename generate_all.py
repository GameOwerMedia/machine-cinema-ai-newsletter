from __future__ import annotations

import argparse
import logging
from pathlib import Path

from newsletter import run
from newsletter.app import GenerationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Machine Cinema AI newsletter")
    parser.add_argument(
        "--mode",
        choices=["curated", "live"],
        default="curated",
        help="Select data source mode. Curated falls back to live when dataset is missing.",
    )
    parser.add_argument(
        "--config",
        default="sources.yml",
        help="Path to sources.yml configuration file.",
    )
    parser.add_argument(
        "--reset-seen",
        action="store_true",
        help="Reset the seen cache before generation.",
    )
    parser.add_argument(
        "--seen-ttl",
        type=int,
        default=None,
        help="Number of days to retain entries in the seen cache (None disables pruning).",
    )
    parser.add_argument(
        "--seen-scope",
        choices=["daily", "rolling"],
        default="rolling",
        help="daily keeps separate cache per day, rolling reuses across days.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    try:
        result = run(args, base_dir=Path.cwd())
    except GenerationError as exc:
        logging.getLogger("newsletter").error("Generation failed: %s", exc)
        return 1
    logging.getLogger("newsletter").info(
        "Newsletter ready for %s with %s posts", result["date"], result["published_count"]
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
