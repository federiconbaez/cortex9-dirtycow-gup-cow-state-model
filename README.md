# cortex9-dirtycow-gup-cow-state-model

An offline state model of the race between `__get_user_pages()` and
`madvise(MADV_DONTNEED)` that led to CVE-2016-5195 ("Dirty COW"). Two
kernel versions are compared:

- **6b25e21:** before the fix. When a fault breaks COW, `faultin_page()`
  drops `FOLL_WRITE`.
- **19be0eaffa3a:** "mm: remove gup_flags FOLL_WRITE games from
  `__get_user_pages()`". It sets `FOLL_COW` instead and lets
  `can_follow_write_pte()` accept only a dirty pte that went through a
  COW cycle.

**No syscalls, `/proc`, mmap or kernel code are used.** The model covers
one page of a private, read-only file mapping as abstract states:

- the pte, which is `none`, `P` (the page-cache page) or `C` (the private
  anon copy), with write and dirty bits;
- the GUP caller's flags.

Two threads run against that state:

- **A:** a `FOLL_WRITE|FOLL_FORCE` GUP caller, stepped as
  follow → fault → follow → … → write;
- **B:** k DONTNEED zaps.

The explorer covers every interleaving. The invariant is: *A never
writes page P*. No verdict is hardcoded.

## Results (`results/`)

| version | zaps | VM_WRITE | violating / schedules (unpopulated pte) |
|---|---|---|---|
| 6b25e21 | 0 | no | 0 / 1 |
| 6b25e21 | 1 | no | 1 / 13 |
| 6b25e21 | 3 | no | 51 / 415 |
| 6b25e21 | 1–3 | yes | 0 |
| 19be0eaffa3a | 0–3 | either | 0 |

The pre-fix counterexample, from `results/counterexamples.txt`, runs as
follows:

1. A does a COW fault, which yields C, read-only and dirty.
2. A's follow fails because there is no write bit.
3. A's `do_wp_page` reuse returns `VM_FAULT_WRITE`, so `FOLL_WRITE` is
   dropped.
4. **B zaps the pte.**
5. A's follow fails on `none`, so A takes a *read* fault, which maps P.
6. A's follow returns P, and A writes P.

`results/zap_position.csv` shows that, with a single zap in a sequential
run, only the zap right after the reuse fault (or right after the
`wp_page_copy` fault when the pte starts populated) gives P. In
19be0eaffa3a, no zap position does.

## Usage

```sh
PYTHONPATH=src python3 -m dirtycow_model explore --version 6b25e21 --zaps 1
PYTHONPATH=src python3 -m dirtycow_model trace --version 6b25e21 --zap-after 3
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/gen_results.py /tmp/out && diff -r results /tmp/out
```

See [SOURCES.md](SOURCES.md), [LIMITATIONS.md](LIMITATIONS.md),
[PRACTICE.md](PRACTICE.md) (Spanish) and [README.es.md](README.es.md).

License: Apache-2.0.
