"""Small explicit-state interleaving explorer (no threads, no OS).

A program is a list of threads; each thread is a list of Steps. A Step has
  name     - label used in traces
  enabled  - state -> bool (e.g. a lock is free)
  choices  - state -> list of choice labels (nondeterminism, default [None])
  apply    - (state, choice) -> None, mutating a copy of the state
Every interleaving and every choice is covered depth-first (thread 0
first, choices in list order); `invariant(state)` is checked after each
step and a schedule stops at its first violation. Identical (state,
program counters) nodes are memoised, so `schedules` and `violating` are
exact path counts computed without re-walking shared suffixes. The
explorer never decides the verdict itself: it reports what it finds.
`finished(state)` marks complete schedules whose thread work did not
reach its goal within the step bound (`unfinished`).
"""
import copy
import json
from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class Step:
    name: object  # str, or callable(state) -> str evaluated before the step
    apply: Callable
    enabled: Callable = lambda s: True
    choices: Callable = lambda s: [None]


@dataclass
class Result:
    schedules: int = 0
    violating: int = 0
    deadlocks: int = 0
    unfinished: int = 0
    states: int = 0
    first_counterexample: Optional[list] = None
    first_violation: Optional[str] = None


def _key(state, pcs):
    return json.dumps(state, sort_keys=True, default=str) + repr(pcs)


def explore(threads: List[List[Step]], init: dict, invariant: Callable,
            finished: Callable = lambda s: True) -> Result:
    res = Result()
    memo = {}

    def dfs(state, pcs, trace):
        k = _key(state, pcs)
        if k in memo:
            return memo[k]
        res.states += 1
        bad = invariant(state)
        if bad:
            if res.first_counterexample is None:
                res.first_counterexample, res.first_violation = list(trace), bad
            memo[k] = (1, 1, 0, 0)
            return memo[k]
        runnable = [t for t, pc in enumerate(pcs) if pc < len(threads[t]) and threads[t][pc].enabled(state)]
        if not runnable:
            dead = int(any(pc < len(threads[t]) for t, pc in enumerate(pcs)))
            memo[k] = (1, 0, dead, int(not dead and not finished(state)))
            return memo[k]
        tot = [0, 0, 0, 0]
        for t in runnable:
            st = threads[t][pcs[t]]
            for ch in st.choices(state):
                s2 = copy.deepcopy(state)
                st.apply(s2, ch)
                p2 = list(pcs)
                p2[t] += 1
                nm = st.name(state) if callable(st.name) else st.name
                label = f"T{t}:{nm}" + (f"[{ch}]" if ch is not None else "")
                for i, x in enumerate(dfs(s2, tuple(p2), trace + [label])):
                    tot[i] += x
        memo[k] = tuple(tot)
        return memo[k]

    res.schedules, res.violating, res.deadlocks, res.unfinished = dfs(copy.deepcopy(init), tuple([0] * len(threads)), [])
    return res
