from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "scripts/share_primary_models.py",
    "scripts/share_barrier_models.py",
    "scripts/charls_context_check.py",
    "scripts/klosa_context_check.py",
    "scripts/all_four_sensitivity.py",
    "scripts/share_revision_checks.py",
]


def main() -> None:
    for script in SCRIPTS:
        subprocess.run([sys.executable, str(PROJECT_ROOT / script)], check=True, cwd=PROJECT_ROOT)


if __name__ == "__main__":
    main()
