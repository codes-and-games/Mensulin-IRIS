import csv
from iris.tools.register_raw import main
from iris.tools.verify_registry import verify

def test_register_then_verify_and_detect_change(tmp_path):
    (tmp_path / "data/raw/ds").mkdir(parents=True); (tmp_path / "data/raw/ds/a.csv").write_text("x\n1\n")
    (tmp_path / "data/sources_registry.csv").write_text("source_id,class,title,citation_or_url,version,access_date,licence,sha256,used_for,verified_by\nS99,PUBLIC_DATASET,t,u,v,,,,x,\n")
    assert main(["ds", "S99", "--root", str(tmp_path)]) == 0
    rows = list(csv.DictReader(open(tmp_path / "data/manifest.csv")))
    assert rows[0]["path"] == "data/raw/ds/a.csv" and rows[0]["source_id"] == "S99"       # POSIX path on every OS
    assert verify(tmp_path).hard_errors() == []
    import os, stat
    f = tmp_path / "data/raw/ds/a.csv"; os.chmod(f, stat.S_IRUSR | stat.S_IWUSR); f.write_text("x\n2\n")
    assert main(["ds", "S99", "--root", str(tmp_path)]) == 1                             # changed file refused, not re-hashed
