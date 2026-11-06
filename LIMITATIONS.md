# Limitations

- **Abstract states only.** There is one page, one mm and one VMA. The
  model leaves out page locks, the TLB, reference counts, the mapcount,
  KSM, swap, THP and hugetlb, as well as `FOLL_POPULATE` and `FOLL_MLOCK`.
  Real exploitation details, and how a write reaches P (for example
  through `/proc/self/mem`), are intentionally out of scope.
- **Atomic steps.** Each follow or fault is treated as atomic (under
  `ptl`). Interleavings within a fault (`do_wp_page` drops `ptl` before
  `wp_page_copy`) are not explored.
- **`wp_page_copy` is assumed to succeed** (`page_copied`, so it returns
  `VM_FAULT_WRITE`). Reuse assumes a single mapping of C.
- **Thread B** models only `MADV_DONTNEED` zapping the pte. Other zappers
  (reclaim, `munmap`) are not modelled.
- **Bounds.** The step bound is 12 GUP steps and at most 3 zaps.
  `unfinished` = 0 means A completed in every schedule under those
  bounds. Schedule counts include no-op steps after A finishes.
- **Later fixes.** The later THP variant (CVE-2017-1000405) and the
  2020+ GUP/COW rework are not modelled.
- **CI.** The workflow runs the tests on Python 3.10–3.13, regenerates
  `results/` and compares it byte by byte. See the Actions page for run
  status.
