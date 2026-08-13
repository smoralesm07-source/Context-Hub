import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from context_hub.censo_migration import _digits

def test_numeric_cut_normalization():
    assert _digits(15101.0,5)=="15101"
    assert _digits("15101.0",5)=="15101"
    assert _digits(15.0,2)=="15"
