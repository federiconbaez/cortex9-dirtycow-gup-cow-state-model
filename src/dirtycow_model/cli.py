"""CLI:
  python -m dirtycow_model explore --version 6b25e21 [--zaps 1] [--vm-write] [--populated]
  python -m dirtycow_model trace --version 19be0eaffa3a [--zap-after 3]
Abstract page-table states only: no syscalls, no /proc, no kernel."""
import argparse
import json

from .mm import VERSIONS
from .scenarios import run, sequential


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="dirtycow_model")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("explore")
    t = sub.add_parser("trace")
    for p in (e, t):
        p.add_argument("--version", choices=VERSIONS, required=True)
        p.add_argument("--vm-write", action="store_true")
        p.add_argument("--populated", action="store_true", help="pte already maps P read-only")
    e.add_argument("--zaps", type=int, default=1, choices=range(0, 4))
    t.add_argument("--zap-after", type=int, default=None)
    a = ap.parse_args(argv)
    if a.cmd == "explore":
        r = run(a.version, a.zaps, a.vm_write, a.populated)
        out = {"schedules": r.schedules, "violating": r.violating, "unfinished": r.unfinished,
               "first_violation": r.first_violation, "first_counterexample": r.first_counterexample}
    else:
        s, tr = sequential(a.version, a.vm_write, a.populated, a.zap_after)
        out = {"written": s["a"]["written"], "trace": tr}
    print(json.dumps(out, indent=2))
    return 0
