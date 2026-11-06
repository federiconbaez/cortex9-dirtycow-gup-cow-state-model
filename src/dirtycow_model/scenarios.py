from .explore import explore
from .mm import finished, gup_thread, initial, invariant, zap_thread


def run(version, zaps=1, vm_write=False, populated=False):
    return explore([gup_thread(), zap_thread(zaps)], initial(version, vm_write, populated),
                   invariant, finished)


def grid():
    for v in ("6b25e21", "19be0eaffa3a"):
        for zaps in (0, 1, 2, 3):
            for vm_write in (False, True):
                for populated in (False, True):
                    yield v, zaps, vm_write, populated


def sequential(version, vm_write=False, populated=False, zap_after=None):
    """Run thread A alone; optionally zap once right after A's step number `zap_after`."""
    from .mm import MAX_GUP_STEPS, gup_label, gup_step
    s = initial(version, vm_write, populated)
    trace = []
    for i in range(MAX_GUP_STEPS):
        if s["a"]["phase"] == "done":
            break
        trace.append(gup_label(s))
        gup_step(s, None)
        if zap_after == i:
            s["pte"] = None
            trace.append("zap")
    return s, trace
