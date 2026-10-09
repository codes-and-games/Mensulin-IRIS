# 02 Environment setup (about 10 minutes)

**Objective:** a working Python environment in which `pytest` passes and the TEST pipeline runs.
**Prerequisites:** Python 3.11 or newer (3.12 was used for preparation), Git. Windows 11 is fine; the commands below are PowerShell.

```powershell
git clone <your-repo-url> iris ; cd iris
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"         # installs the package; no PYTHONPATH needed afterwards
python -m pytest tests -q                  # expect: all tests pass (100 at preparation time)
python -m iris.tools.run_all --mode test --smoke   # plumbing check, NEVER a result
```
macOS/Linux: replace the activation line with `source .venv/bin/activate`.

If you do not want to use `-e`, set `$env:PYTHONPATH="src"` (PowerShell) or `export PYTHONPATH=src` before every command.
Exact tested versions are in `requirements-lock.txt`: `python -m pip install -r requirements-lock.txt` reproduces the preparation environment.

**Success:** all tests passed; `run_all` prints a table in which every TEST/smoke row says `none (TEST/smoke: plumbing only)` under evidence status.
**Failure:** an import error means the install step did not finish; re-run it. `ModuleNotFoundError: iris` means you are outside the virtual environment.
**Windows note:** `make` is not available by default. Every Makefile target has a `python -m ...` equivalent in this documentation; use those.
**Climate extras (only for step 6):** `python -m pip install -e ".[climate]"` (adds xarray, netCDF4, cdsapi).
**Next:** `docs/START_HERE.md` step 1.
