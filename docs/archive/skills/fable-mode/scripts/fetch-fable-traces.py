#!/usr/bin/env python3
"""fetch-fable-traces.py — download the public Fable 5 trace dataset locally.

Pulls Glint-Research/Fable-5-traces (4,665 real Fable 5 Claude Code events,
chain-of-thought intact) from Hugging Face to a local directory for analysis.

LICENSE BOUNDARY — read before redistributing anything. The dataset is AGPL-3.0.
This repo therefore never bundles it: you download it yourself, directly from the
source, by running this script. Keep the data OUT of git (the default target dir
is outside any repo). Insights distilled in your own words are yours; verbatim
trace excerpts are derivatives of the dataset and carry AGPL obligations.

Usage:
    python3 fetch-fable-traces.py                    # full dataset (~70 MB)
    python3 fetch-fable-traces.py --sample 500       # streamed sample, no full pull
    python3 fetch-fable-traces.py --target-dir DIR   # custom destination

Output: JSONL at <target-dir>/fable-5-traces.jsonl, one event per line with the
dataset's ten fields (uid, session, model, cot, output_type, output, ...). Rows
within a session are NOT pre-sorted; sort by the integer after '#' in uid to
recover execution order.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DATASET_ID = "Glint-Research/Fable-5-traces"
DEFAULT_TARGET_DIR = Path.home() / ".cache" / "fable-traces"
OUTPUT_FILENAME = "fable-5-traces.jsonl"


def fetch(target_dir: Path, sample: int | None) -> Path:
    """Download the dataset (or a streamed sample) and write it as JSONL."""
    try:
        from datasets import load_dataset
    except ImportError:
        sys.exit(
            "The 'datasets' library is required. Install it first:\n"
            "    pip install --user datasets\n"
            "then re-run this script."
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / OUTPUT_FILENAME

    if sample:
        # Streaming never materialises the full 70 MB — good for a first look.
        rows = load_dataset(DATASET_ID, split="train", streaming=True)
        with output_path.open("w", encoding="utf-8") as handle:
            for row_index, row in enumerate(rows):
                if row_index >= sample:
                    break
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return output_path

    rows = load_dataset(DATASET_ID, split="train")
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download the public Fable 5 trace dataset for local analysis.",
    )
    parser.add_argument(
        "--sample",
        type=int,
        help="stream only the first N rows instead of the full dataset",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=DEFAULT_TARGET_DIR,
        help=f"destination directory (default: {DEFAULT_TARGET_DIR})",
    )
    args = parser.parse_args()

    output_path = fetch(args.target_dir, args.sample)
    row_count = sum(1 for _ in output_path.open(encoding="utf-8"))
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Wrote {row_count} events ({size_mb:.1f} MB) to {output_path}")
    print("Dataset license: AGPL-3.0 — analyse locally, do not redistribute.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
