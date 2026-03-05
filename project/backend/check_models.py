"""Run this locally (outside Docker) to find the right scikit-learn version.

Usage:
    python check_models.py
"""
import joblib, pathlib, sys

models_dir = pathlib.Path("models")
for name in ("railway_clf", "industrial_clf", "aggression_clf"):
    p = models_dir / f"{name}.joblib"
    if not p.exists():
        print(f"MISSING: {p}")
        continue
    try:
        obj = joblib.load(p)
        print(f"OK: {name} -> {type(obj).__module__}.{type(obj).__name__}")
    except Exception as e:
        print(f"ERROR: {name} -> {e}")

# Also print current sklearn version
try:
    import sklearn
    print(f"\nCurrent scikit-learn: {sklearn.__version__}")
except ImportError:
    print("scikit-learn not installed")
