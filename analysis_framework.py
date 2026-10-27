"""Small framework for inspecting the aggregate source data."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_FILES = (
    "table_1_source.csv",
    "table_2_source.csv",
    "figure_2_primary_models.csv",
    "supplementary_figure_s5_cross_cohort_context_checks.csv",
)


def load_sources(source_dir: Path, names: tuple[str, ...] = DEFAULT_FILES) -> dict[str, pd.DataFrame]:
    """Load the aggregate files used for the main reported results."""
    sources = {}
    for name in names:
        path = source_dir / name
        if not path.exists():
            raise FileNotFoundError(path)
        sources[name] = pd.read_csv(path)
    return sources


def source_manifest(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return a compact record of the loaded source files."""
    return pd.DataFrame(
        {
            "file": list(sources),
            "rows": [len(frame) for frame in sources.values()],
            "columns": [len(frame.columns) for frame in sources.values()],
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect aggregate source data.")
    parser.add_argument("--source-dir", type=Path, default=Path("source_data"))
    parser.add_argument("--output", type=Path, default=Path("source_manifest.csv"))
    args = parser.parse_args()

    sources = load_sources(args.source_dir)
    manifest = source_manifest(sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(args.output, index=False)
    print(manifest.to_string(index=False))


if __name__ == "__main__":
    main()
