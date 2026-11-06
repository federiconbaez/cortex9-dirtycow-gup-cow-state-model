"""Regenerate results/ (deterministic). Usage: gen_results.py [outdir]"""
import csv
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dirtycow_model.mm import MAX_GUP_STEPS  # noqa: E402
from dirtycow_model.scenarios import grid, run, sequential  # noqa: E402

out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results"
out.mkdir(parents=True, exist_ok=True)
with open(out / "grid.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["version", "zaps", "vm_write", "populated", "schedules", "violating", "unfinished"])
    for g in grid():
        r = run(*g)
        w.writerow(list(g) + [r.schedules, r.violating, r.unfinished])
with open(out / "zap_position.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["version", "populated", "zap_after_step", "written"])
    for v in ("6b25e21", "19be0eaffa3a"):
        for pop in (False, True):
            for k in [None] + list(range(MAX_GUP_STEPS)):
                s, _ = sequential(v, populated=pop, zap_after=k)
                w.writerow([v, pop, "" if k is None else k, s["a"]["written"]])
with open(out / "counterexamples.txt", "w") as f:
    for v, pop in (("6b25e21", False), ("6b25e21", True), ("19be0eaffa3a", False)):
        r = run(v, 1, False, pop)
        f.write(f"## version={v} zaps=1 populated={pop}: {r.first_violation or 'no violation'}\n")
        f.writelines(f"  {x}\n" for x in (r.first_counterexample or []))
FILES = ("grid.csv", "zap_position.csv", "counterexamples.txt")
(out / "SHA256SUMS").write_text("".join(
    f"{hashlib.sha256((out / n).read_bytes()).hexdigest()}  {n}\n" for n in FILES))
