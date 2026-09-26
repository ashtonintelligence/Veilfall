"""Compatibility entrypoint for the v021 atlas; current release is v0.2.7."""
from pathlib import Path
import runpy
import sys
source=Path(__file__).resolve().parents[1]/'v026'
sys.path.insert(0,str(source))
runpy.run_path(str(source/'build_assets.py'),run_name='__main__')
