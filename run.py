#!/usr/bin/env python3
"""Start the demo; Streamlit opens http://localhost:8501 in your browser."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(ROOT / "login.py"),
            "--server.headless=false",
        ],
        cwd=ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
