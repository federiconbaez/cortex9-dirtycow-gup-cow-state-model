# Sources

All files were fetched once and read offline. The SHA-256 hashes are of
the local copies.

| File | Upstream | SHA-256 |
|---|---|---|
| linux-19be0eaffa3a.diff | torvalds/linux commit 19be0eaffa3ac7d8eb6784ad9bdbc7d67ed8e619 (parent 6b25e21fa6f26d0f0d45f161d169029411c84286) | 79624811b4f82feddb8b335781e3f6fe3c6beaa512ef95b98db49c3a907bb59a |
| mm/gup.c @ 6b25e21 | same repository | 4b05f6c6bb41487c608c18a1e6006dc8c840aacbcbf2dff27160ac5253398f0d |
| mm/memory.c @ 6b25e21 | same | f8fb2fe8284347d1c2cbcfcb140f750faa7c92f9fa95d737649475c63db49f9d |
| mm/gup.c @ 19be0eaffa3a | same | f1f6fe1a98cf17b4fef7de3345b1b5d7eb0745827447d0d48bd3650a12a3f515 |
| NVD CVE-2016-5195 JSON | services.nvd.nist.gov | 3eb306f0f13bb47b2ffab79b07cd5066d11fdf24b7a27b622e1de8ac0c2af288 |

## Source-to-model trace

| Source | Model (`mm.py`) |
|---|---|
| gup.c 6b25e21 l.569-585, retry: `follow_page_mask` / `faultin_page` / `goto retry` | phases follow → fault → follow |
| gup.c 6b25e21 follow_page_pte l.63-110, `(FOLL_WRITE && !pte_write) → NULL` | `_follow`, version 6b25e21 |
| gup.c 19be0eaffa3a l.67-70 `can_follow_write_pte`, l.108 | `_can_follow` |
| gup.c 6b25e21 l.414-415, `VM_FAULT_WRITE && !VM_WRITE → ~FOLL_WRITE` | `a["WRITE"] = False` |
| gup.c 19be0eaffa3a l.425, `*flags \|= FOLL_COW` | `a["COW"] = True` |
| memory.c do_fault l.3317-3330 | `_fault` with a none pte |
| memory.c do_cow_fault l.3204 → alloc_set_pte l.3033 `maybe_mkwrite(pte_mkdirty())` | C, dirty, write = VM_WRITE |
| memory.c handle_pte_fault l.3540-3543 → do_wp_page l.2363 | `_fault` with a present pte |
| memory.c wp_page_reuse l.2077 … `return VM_FAULT_WRITE` l.2123 | anon C reuse |
| memory.c wp_page_copy l.2142 … `return page_copied ? VM_FAULT_WRITE : 0` l.2261 | P → C copy (assumed to succeed) |

Exploit-database and Packet Storm references in the NVD record were not
fetched or used.
