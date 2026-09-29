#!/usr/bin/env python3
"""Install the reviewed gstack advisory references, without upstream execution."""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sigma_runtime.gstack import install  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=None)
    args = parser.parse_args()
    print(install(ROOT, args.cache_dir))


if __name__ == "__main__":
    main()
