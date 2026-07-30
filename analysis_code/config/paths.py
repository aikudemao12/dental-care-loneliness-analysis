from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def env_path(name: str, default: Path) -> Path:
    return Path(os.environ.get(name, default)).expanduser()


@dataclass(frozen=True)
class Paths:
    project_root: Path = Path(__file__).resolve().parents[1]
    data_root: Path = env_path("COHORT_DATA_ROOT", project_root / "data")
    tables_root: Path = env_path("TABLES_ROOT", project_root / "outputs" / "tables")
    share_analytic: Path = env_path("SHARE_ANALYTIC_CSV", data_root / "share_analysis_dataset.csv")
    charls_analytic: Path = env_path("CHARLS_ANALYTIC_CSV", data_root / "charls_context_dataset.csv")
    klosa_analytic: Path = env_path("KLOSA_ANALYTIC_CSV", data_root / "klosa_context_dataset.csv")


PATHS = Paths()
