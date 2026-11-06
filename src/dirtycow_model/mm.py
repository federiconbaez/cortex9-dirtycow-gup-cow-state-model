"""One page of a private file mapping, a FOLL_FORCE|FOLL_WRITE GUP caller and a zapper.

Abstract objects (not kernel memory):
  "P" - the page-cache page of the file (must never be written through a
        private mapping)
  "C" - an anonymous COW copy private to this mm
A pte is None or {"page": "P"|"C", "write": bool, "dirty": bool}.

Thread A = __get_user_pages() with FOLL_WRITE|FOLL_FORCE on a VMA mapped
           MAP_PRIVATE without VM_WRITE (unless vm_write=True), source
           Linux at 6b25e21 (parent of 19be0eaffa3a) and at 19be0eaffa3a:
  gup.c  l.569-585 retry: follow_page_mask(); if NULL -> faultin_page(); case 0: goto retry
         follow_page_pte l.63-110: pte none -> NULL; (FOLL_WRITE && !pte_write) -> NULL
           fix l.108: (FOLL_WRITE && !can_follow_write_pte(pte, flags)) -> NULL
           can_follow_write_pte l.67-70: pte_write || (FOLL_FORCE && FOLL_COW && pte_dirty)
         faultin_page l.354-416: FOLL_WRITE -> FAULT_FLAG_WRITE; handle_mm_fault;
           l.414-415 (VM_FAULT_WRITE && !VM_WRITE) -> *flags &= ~FOLL_WRITE
           fix l.425: ... -> *flags |= FOLL_COW
  memory.c do_fault l.3317-3330: !WRITE -> do_read_fault (maps P read-only, clean);
             private WRITE -> do_cow_fault l.3204 -> alloc_set_pte l.3033
             maybe_mkwrite(pte_mkdirty()) : dirty, write only if VM_WRITE
           handle_pte_fault l.3540-3543: WRITE && !pte_write -> do_wp_page
           do_wp_page l.2363: anon page with a single mapping -> wp_page_reuse,
             returns VM_FAULT_WRITE (l.2123); file page -> wp_page_copy (new
             dirty anon copy C, returns VM_FAULT_WRITE)
  then the caller writes through the returned page.
Thread B = madvise(MADV_DONTNEED) on the same page: zap -> pte none.
           Both threads hold mmap_sem for read, so they do not exclude each other.
"""
from .explore import Step

VERSIONS = ("6b25e21", "19be0eaffa3a")
MAX_GUP_STEPS = 12


def initial(version, vm_write=False, populated=False):
    return {"version": version, "vm_write": vm_write,
            "pte": {"page": "P", "write": False, "dirty": False} if populated else None,
            "a": {"phase": "follow", "WRITE": True, "FORCE": True, "COW": False,
                  "got": None, "written": None, "loops": 0},
            "zaps": 0}


def _can_follow(s, pte):
    a = s["a"]
    if s["version"] == "6b25e21":
        return pte["write"]
    return pte["write"] or (a["FORCE"] and a["COW"] and pte["dirty"])


def _follow(s):
    a, pte = s["a"], s["pte"]
    if pte is None:
        return None
    if a["WRITE"] and not _can_follow(s, pte):
        return None
    return pte["page"]


def _fault(s):
    """handle_mm_fault for one page; returns True if VM_FAULT_WRITE."""
    a, pte, vw = s["a"], s["pte"], s["vm_write"]
    write = a["WRITE"]
    if pte is None:
        if not write:
            s["pte"] = {"page": "P", "write": False, "dirty": False}  # do_read_fault
            return False
        s["pte"] = {"page": "C", "write": vw, "dirty": True}            # do_cow_fault
        return False
    if write and not pte["write"]:
        if pte["page"] == "C":
            pte["write"] = vw                                          # wp_page_reuse
            pte["dirty"] = True
            return True
        s["pte"] = {"page": "C", "write": vw, "dirty": True}            # wp_page_copy
        return True
    return False


def gup_step(s, c):
    a = s["a"]
    if a["phase"] == "done":
        return
    if a["phase"] == "follow":
        page = _follow(s)
        a["loops"] += 1
        if page is None:
            a["phase"] = "fault"
        else:
            a["got"], a["phase"] = page, "write"
        return
    if a["phase"] == "fault":
        vm_fault_write = _fault(s)
        if vm_fault_write and not s["vm_write"]:
            if s["version"] == "6b25e21":
                a["WRITE"] = False
            else:
                a["COW"] = True
        a["phase"] = "follow"
        return
    if a["phase"] == "write":
        a["written"], a["phase"] = a["got"], "done"


def gup_label(s):
    a = s["a"]
    flags = "|".join(f for f in ("WRITE", "FORCE", "COW") if a[f])
    pte = s["pte"]
    p = "none" if pte is None else f"{pte['page']}{'w' if pte['write'] else 'r'}{'d' if pte['dirty'] else 'c'}"
    return f"{a['phase']} flags={flags} pte={p}"


def gup_thread():
    return [Step(gup_label, apply=gup_step) for _ in range(MAX_GUP_STEPS)]


def zap_thread(n):
    def zap(s, c):
        s["pte"] = None
        s["zaps"] += 1
    return [Step("madvise(DONTNEED) zap", apply=zap) for _ in range(n)]


def finished(s):
    return s["a"]["phase"] == "done"


def invariant(s):
    if s["a"]["written"] == "P":
        return "wrote page-cache page P through a read-only private mapping"
    return None
