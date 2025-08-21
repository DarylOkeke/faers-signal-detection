#!/usr/bin/env python3
"""Entrypoint to regenerate analysis figures."""
from analysis.minoxidil_analysis import main as run_minoxidil


def main() -> int:
    return run_minoxidil()


if __name__ == "__main__":
    raise SystemExit(main())
