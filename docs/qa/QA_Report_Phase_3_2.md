# V3.0 Phase 3.2 — Project Graph QA Report

## Final Verdict

**PASS**

The initial DeepSeek review returned **PASS WITH ISSUES** with zero Critical findings.
Two identity issues, D1 and D2, had to be resolved before snapshot work. Codex completed
the directed Phase 3.2.1 hardening, and the subsequent DeepSeek retest verified both
fixes with no remaining retest blocker.

The QA sequence was:

```text
Initial DeepSeek QA: PASS WITH ISSUES
    -> D1 containment attribution
    -> D2 external import identity
Codex Phase 3.2.1 fix
DeepSeek targeted retest: PASS
```

## Review Scope

The QA cycle covered:

- `ProjectGraph`, `GraphNode`, and `GraphEdge`;
- the four graph node kinds and two relation kinds;
- project-to-file, file-to-symbol, and class-to-child containment;
- Python AST import discovery and relative import identity;
- Java best-effort import discovery;
- internal-file versus unresolved-target resolution;
- stable `SymbolId` reuse, including Java overloads and fallback-line collisions;
- deterministic node/edge identity, deduplication, equality, and ordering;
- empty projects and regression isolation from existing application behavior.

The review did not expand scope into snapshots, graph persistence, semantic dependency
analysis, RAG, agents, routers, APIs, VS Code, or automatic source changes.

## Environment

| Item | Result |
|---|---|
| Branch | `v3.0.0-test1` |
| Initial implementation | `5531e608e94c2737a98016f84853384d439a4df8` |
| Hardening implementation | `dd76fabb3ee607297e455fd0844be76e53394131` |
| Final full suite | `60 passed` |
| Final Graph tests | `13 passed` |
| Offline LLM-contract smoke | `6 passed` |
| Network/provider calls | None |

The Codex host uses Anaconda Python 3.13 and can segfault while pytest loads its
debugging plugin through `readline`/locale integration. This is a confirmed host issue,
not a project failure. Validation used `-p no:debugging` as an invocation-side
workaround; `pytest.ini` was not changed.

## Initial DeepSeek QA

The initial QA reviewed commit `5531e608e94c2737a98016f84853384d439a4df8`
(`feat(v3): add project relationship graph`).

- Verdict: **PASS WITH ISSUES**
- Critical: **0**
- Required before Snapshot: D1 and D2

The initial implementation otherwise established the intended small, deterministic,
in-memory graph and preserved existing regression behavior.

## Initial Findings

### D1 — Duplicate class containment attribution

`SymbolId` already distinguished repeated class and method declarations using
`fallback_line`. However, class containment used a dictionary keyed only by bare
`qualified_name`. A later duplicate class replaced the earlier entry, so a method from
the first class could be attached to the second class node.

### D2 — Relative unresolved external identity

Python relative-import resolution calculated a canonical target for local lookup, but
an unresolved `EXTERNAL_MODULE` node could still use raw relative spelling such as
`..services.user`. This made the future snapshot-facing graph identity policy
inconsistent.

## Critical / Medium / Low

- Critical findings: **0**.
- Medium findings: the supplied QA result did not assign a separate Medium count.
- D1 and D2: explicitly required correction before Phase 3.3, without inventing a
  severity label not present in the original QA record.
- Remaining Low/deferred observations include self-import loops, star-import
  granularity, and coarse external-module modeling.

## Fix Summary

Codex implemented Phase 3.2.1 in commit
`dd76fabb3ee607297e455fd0844be76e53394131`
(`fix(v3): harden graph identity and containment`).

For D1, containment now retains all class candidates with a matching parent qualified
name, filters them using the existing child and candidate line ranges, selects the
nearest enclosing class, and uses that class's `SymbolId` node. The parser and
`SymbolId` design were unchanged.

For D2, the canonical relative import target is now the shared identity used by both
local file lookup and unresolved `EXTERNAL_MODULE` creation. When importer context is
insufficient, a deterministic unresolved-relative descriptor is retained instead of
inventing a module mapping.

Five offline regression tests were added for duplicate class containment, cross-file
isolation, relative external identity, documented self/star behavior, Unicode paths,
and duplicate alias invariance.

## Retest

DeepSeek performed a targeted retest of the hardening commit.

- Final verdict: **PASS**
- D1 fix: **VERIFIED**
- D2 policy: **VERIFIED**
- Retest blocker: **NONE**

The retest closed the two issues carried by the initial **PASS WITH ISSUES** verdict.

## Regression

Final local regression evidence:

- Complete suite: `60 passed`.
- Graph suite: `13 passed`.
- Offline LLM-contract smoke: `6 passed`.
- Existing Java overload behavior passed.
- Existing nested-class behavior passed.
- Same class names across files remained isolated.
- Empty-project and deterministic-rebuild tests passed.

No real LLM call, credential, network request, or provider interaction occurred.

## Determinism

The final implementation uses existing domain identities, set-based deduplication, and
stable node/edge sorting. Duplicate imports and aliases do not create duplicate edges.
Relative Python targets are canonicalized using deterministic importer context before
identity creation. Duplicate class containment is selected from existing stable symbol
ranges and linked through the selected class `SymbolId`.

Repeated graph builds for an unchanged project produce equal nodes, edges, ordering,
and statistics.

## Remaining Known Limitations

- Self-import produces an explicit self-loop `IMPORTS` edge.
- Star imports remain coarse targets such as `a.*`.
- `EXTERNAL_MODULE` does not model package members.
- Python `src` layouts are not resolved.
- `pyproject` packaging semantics are not interpreted.
- Namespace packages are not resolved.
- `site-packages` resolution is not performed.
- Root `__init__.py` relative imports retain a narrow precision gap.
- Java import discovery and parsing remain best-effort compatibility.
- No `CALLS`, `REFERENCES`, `INHERITS`, or `IMPLEMENTS` edges exist.
- `Project.id` depends on the resolved absolute project root path.

Because of the location-dependent project identity, the first Phase 3.3 Snapshot version
should guarantee time-series comparison only under the same project root. This QA did
not request or implement a `Project.id` redesign.

## Next Phase Recommendation

The Phase 3.2 QA loop is closed with final **PASS**. Phase 3.3 Project Snapshot / State
may formally begin after this documentation gate is committed.

This report does not claim that Phase 3.3 has started.
