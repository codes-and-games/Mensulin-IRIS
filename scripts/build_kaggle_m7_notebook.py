"""Regenerate notebooks/iris_kaggle_m7_training.ipynb. The notebook embeds the M7 files (so it also works before they are pushed to GitHub).
Run from the repo root:  python scripts/build_kaggle_m7_notebook.py"""
import base64, io, zipfile
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ["src/iris/features/next_day.py", "src/iris/evaluate/cluster_bootstrap.py",
           "experiments/M7_next_day_tdd_ml/config.yaml", "experiments/M7_next_day_tdd_ml/run.py",
           "experiments/M7_next_day_tdd_ml/README.md", "experiments/M7_next_day_tdd_ml/expected_outputs.md",
           "tests/leakage/test_next_day_features.py"]


def overlay_b64() -> str:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in OVERLAY:
            z.write(ROOT / rel, rel)
    s = base64.b64encode(buf.getvalue()).decode()
    return "\n".join(s[i:i + 100] for i in range(0, len(s), 100))


MD0 = """# IRIS on Kaggle: real-data ML benchmark (M7) + current-state reruns (M4, M1, M6)

**What this does (press *Run All*, nothing to edit):** clones the repo, places the two attached OPEN datasets, ingests them in **provisional** mode,
then runs M4 (leakage checks), M1 (naive baseline), **M7 (next-day TDD: ridge / random forest / gradient boosting vs persistence, participant-held-out)** and M6.

**Before you run:** attach two private datasets with *Add Input*: HUPA-UCM (`HUPA0001P.csv ...`, the 25 *Preprocessed* files) and BrisT1D-Open (the 20 `P*.csv` files from `device_data/processed_state`).
Any folder layout works: files are found by name and checked against the SHA-256 hashes in the repo manifest. Settings: Accelerator **None**, Internet **On**.

**Honest scope.** Provisional run (source sign-off S15/S17 is still open). No menstrual-cycle labels exist in these data, so **nothing here says anything about the cycle**.
TDD under automated insulin delivery reflects controller behaviour as well as physiology. A model that does not beat a trailing mean is a legitimate result."""

C_CFG = '''import os, pathlib, sys, subprocess, shutil, json, platform, hashlib, csv
REPO_URL    = os.environ.get("IRIS_REPO_URL", "https://github.com/codes-and-games/Mensulin-IRIS.git")
BASE_COMMIT = "d625ea9ada8b439cccddbc9a1b17bd62932c382e"  # pinned repository revision for reproducibility
INPUT_ROOT  = pathlib.Path(os.environ.get("IRIS_INPUT_ROOT", "/kaggle/input"))
WORK_ROOT   = pathlib.Path(os.environ.get("IRIS_WORK_ROOT", "/kaggle/working"))
VERIFY_HASHES = os.environ.get("IRIS_VERIFY_HASHES", "1") == "1"
def sh(cmd, check=True, tail=6000):
    print("$", cmd); r = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    print((r.stdout or "")[-tail:], (r.stderr or "")[-2500:])
    if check and r.returncode: raise SystemExit(f"command failed ({r.returncode}): {cmd}")
    return r'''

C_CLONE = '''os.chdir(WORK_ROOT)
sh(f"rm -rf iris && git clone {REPO_URL} iris")
os.chdir(WORK_ROOT / "iris")
sh(f"git checkout --detach {BASE_COMMIT}")
# ---- M7 files (embedded; written only if the repository does not already contain them) -----------------------------------
OVERLAY_B64 = """
@@OVERLAY@@
"""
if not pathlib.Path("experiments/M7_next_day_tdd_ml/run.py").exists():
    import base64, io, zipfile
    zipfile.ZipFile(io.BytesIO(base64.b64decode("".join(OVERLAY_B64.split())))).extractall(".")
    print("M7 files written from the notebook")
else:
    print("M7 already in the repository checkout")
sh(f"{sys.executable} -m pip install -q -e . pytest")
print(platform.python_version(), subprocess.run("git rev-parse HEAD", shell=True, capture_output=True, text=True).stdout.strip())'''

C_DATA = '''# Find each file the repo's manifest lists for the two mapped folders (by name, anywhere under /kaggle/input), check its SHA-256, copy it into place.
MAPPED = ("data/raw/hupa_ucm/Preprocessed/", "data/raw/brist1d/device_data/processed_state/")
want = [r for r in csv.DictReader(open("data/manifest.csv")) if r["path"].endswith(".csv") and r["path"].startswith(MAPPED)]
index = {}
for f in INPUT_ROOT.rglob("*.csv"):
    index.setdefault(f.name, []).append(f)
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
missing, bad = [], []
for r in want:
    name = pathlib.Path(r["path"]).name; cands = index.get(name, [])
    pick = next((c for c in cands if sha(c) == r["sha256"]), None) if VERIFY_HASHES else (cands[0] if cands else None)
    if pick is None:
        (bad if cands else missing).append(name); continue
    dst = pathlib.Path(r["path"]); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(pick, dst)
n = {k: sum(1 for r in want if r["path"].startswith(k)) for k in MAPPED}
print("expected files:", n, "| missing:", missing, "| found but hash differs:", bad)
if missing or bad:
    raise SystemExit("attach the unmodified HUPA-UCM (25 Preprocessed CSVs) and BrisT1D-Open (20 processed_state CSVs) datasets")
print("all raw files present" + (" and match the registered SHA-256" if VERIFY_HASHES else " (hash check OFF)"))'''

C_INGEST = '''for ds in ("hupa_ucm", "brist1d"):
    sh(f"{sys.executable} -m iris.tools.ingest_dataset {ds} --mode provisional")
sh(f"{sys.executable} -m iris.tools.ingest_dataset brist1d --mode provisional --combine")
sh(f"{sys.executable} -m iris.tools.validate_person_day data/processed/person_day.parquet")'''

C_RUN = '''# BLOCKED is a legitimate outcome (the repo refuses to invent an input); it is printed, never hidden
sh(f"{sys.executable} -m pytest -q tests/leakage/test_next_day_features.py", check=False)
for exp in ("M4_leakage", "M1_baseline", "M7_next_day_tdd_ml", "M6_circadian_recovery"):
    sh(f"{sys.executable} -m iris.tools.run_experiment {exp} --mode provisional", check=False)'''

C_SHOW = '''import pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_colwidth", 70)
info = lambda r: json.loads((r / "provenance.json").read_text())["run"]
runs = sorted(pathlib.Path("results/runs").glob("*"), key=lambda p: p.stat().st_mtime)
latest = {}
for r in runs: latest[info(r)["experiment"]] = r
for e, r in latest.items():
    print(f"{e:28s} {info(r)['status']:10s} {info(r)['run_mode']:12s} {r.name}  warnings={info(r)['warnings']}")
t4 = pd.read_parquet(latest["M4_leakage"] / "tables" / "leakage_tests.parquet"); print("\\nM4 leakage checks passed:", int(t4.passed.sum()), "/", len(t4))
print("M1 baseline:"); print(pd.read_parquet(latest["M1_baseline"] / "tables" / "baseline_scores.parquet").round(4).to_string(index=False))
m7 = latest["M7_next_day_tdd_ml"]
T = lambda n: pd.read_parquet(m7 / "tables" / f"{n}.parquet")
print("\\n== M7 cohort flow");  print(T("cohort_flow").to_string(index=False))
print("\\n== M7 feature audit"); print(T("feature_audit").round(3).to_string(index=False))
print("\\n== M7 scores (primary = LeaveOneGroupOut; skill > 0 means lower error than the baseline)"); s = T("scores"); print(s[s.scheme == "LeaveOneGroupOut"][["model","n","mae_u","rmse_u","mape_pct","skill_vs_P1_mae","skill_vs_P7_mae","skill_vs_P7_lo","skill_vs_P7_hi"]].round(3).to_string(index=False))
print("\\n== M7 VERDICT (fixed rule, primary scheme)"); v = T("verdict"); print(v[v.primary].round(3).to_string(index=False))
print("\\n== M7 placebo (must show no skill)"); print(T("placebo_control").round(3).to_string(index=False))
print("\\n== M7 by dataset"); d = T("scores_by_dataset"); print(d[["dataset","model","n_people","n","mae_u","mape_pct"]].round(3).to_string(index=False))'''

C_PACK = '''out = WORK_ROOT / "out"; out.mkdir(exist_ok=True)
sh(f"{sys.executable} -m pip freeze > {out}/pip_freeze.txt")
json.dump({"repo": REPO_URL, "base_commit": BASE_COMMIT, "python": platform.python_version(), "platform": platform.platform(),
           "mode": "provisional", "hash_check": VERIFY_HASHES}, open(out / "environment.json", "w"), indent=2)
shutil.copytree("results/runs", out / "runs", dirs_exist_ok=True)
shutil.copytree("data/processed", out / "processed_qc", dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.parquet"))   # QC reports only
shutil.make_archive(str(WORK_ROOT / "iris_kaggle_outputs"), "zip", out)
print("download iris_kaggle_outputs.zip from the Output tab (no raw data inside)")'''

nb = nbf.v4.new_notebook()
nb["cells"] = [nbf.v4.new_markdown_cell(MD0), nbf.v4.new_code_cell(C_CFG), nbf.v4.new_code_cell(C_CLONE.replace("@@OVERLAY@@", overlay_b64())),
               nbf.v4.new_code_cell(C_DATA), nbf.v4.new_code_cell(C_INGEST), nbf.v4.new_code_cell(C_RUN), nbf.v4.new_code_cell(C_SHOW),
               nbf.v4.new_code_cell(C_PACK)]
nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}
out = ROOT / "notebooks" / "iris_kaggle_m7_training.ipynb"
nbf.write(nb, out)
print("wrote", out, out.stat().st_size, "bytes")
