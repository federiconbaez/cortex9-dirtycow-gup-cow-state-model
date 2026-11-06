import json
import pathlib
import unittest

from dirtycow_model.mm import MAX_GUP_STEPS
from dirtycow_model.scenarios import grid, run, sequential

ROOT = pathlib.Path(__file__).resolve().parents[1]
FX = json.loads((ROOT / "fixtures/cases.json").read_text())


class Fixtures(unittest.TestCase):
    def test_sequential(self):
        for c in FX["sequential"]:
            s, _ = sequential(c["version"], zap_after=c["zap_after"])
            with self.subTest(id=c["id"]):
                self.assertEqual(s["a"]["written"], c["written"])

    def test_explore(self):
        for c in FX["explore"]:
            r = run(c["version"], c["zaps"], c["vm_write"], c["populated"])
            with self.subTest(id=c["id"]):
                self.assertEqual(r.violating > 0, c["violation"])
                self.assertEqual(r.unfinished, 0)


class Properties(unittest.TestCase):
    def test_counterexample_mechanism(self):
        t = run("6b25e21", 1).first_counterexample
        z = t.index("T1:madvise(DONTNEED) zap")
        # before the zap FOLL_WRITE was dropped by a fault on C; after it, a read fault maps P
        self.assertTrue(any("fault flags=WRITE|FORCE pte=C" in x for x in t[:z]))
        self.assertIn("T0:fault flags=FORCE pte=none", t[z + 1:])
        self.assertTrue(t[-1].startswith("T0:write") and "pte=P" in t[-1])

    def test_post_never_violates(self):
        for g in grid():
            r = run(*g)
            self.assertEqual(r.unfinished, 0, g)
            if g[0] == "19be0eaffa3a" or g[2]:
                self.assertEqual(r.violating, 0, g)

    def test_every_zap_position_post(self):
        for k in range(MAX_GUP_STEPS):
            for pop in (False, True):
                s, _ = sequential("19be0eaffa3a", populated=pop, zap_after=k)
                self.assertNotEqual(s["a"]["written"], "P", (k, pop))


if __name__ == "__main__":
    unittest.main()
