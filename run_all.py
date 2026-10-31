"""Run the whole pipeline: clean -> SQL marts -> dashboard -> Power BI model."""
import runpy
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC))
for step in ("01_clean.py", "02_build_marts.py", "04_insights.py", "03_build_dashboard.py", "05_powerbi_model.py"):
    print(f"\n=== {step} ===")
    runpy.run_path(str(SRC / step), run_name="__main__")
