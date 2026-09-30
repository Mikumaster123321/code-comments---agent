# V3.1.0 Phase 0.0 — Development Baseline Gate

## Verdict

**PASS**

V3.1.0 development is open on `v3.1.0-dev`. Phase 0.0 establishes only the development
and research baseline. V3.1.0 Phase 0 Architecture & Research Review has not started,
and no RAG implementation exists.

## Release and Synchronization Gates

| Check | Result |
| --- | --- |
| Previous release | V3.0.1 `RELEASED / FROZEN` |
| Released version metadata | `3.0.1` |
| V3.0.1 release commit | `397beea1b623a6d53ca4b1dbfde3c8c445dd8ff1` |
| `v3.0.1` tag | Annotated; resolves to the release commit |
| V3.0.1 Final Release Gate | `PASS` |
| V3.0.1 final baseline | `414 passed` |
| V3.0.1 Release Blockers | `0` |
| Stable `main` commit | `381708bb5cd57f9c15a8755416434ede5a337824` |
| Local `main` synchronization | PASS; release commit is an ancestor |
| Gitee `main` synchronization | PASS; remote head is the stable `main` commit |
| GitHub `main` synchronization | PASS; remote head is the stable `main` commit |
| Previous development branch | `v3.0.1-dev` retained locally and on both remotes |
| New development branch | `v3.1.0-dev` |
| Branch base | `381708bb5cd57f9c15a8755416434ede5a337824` |
| `main` / branch merge-base | `381708bb5cd57f9c15a8755416434ede5a337824` |
| Release commit in new branch ancestry | PASS |

The immutable annotated tags remain unchanged:

- `v3.0.0` resolves to `2b2b0cb103264f7ac278f35c19a1dc0b02196dc8`.
- `v3.0.1` resolves to `397beea1b623a6d53ca4b1dbfde3c8c445dd8ff1`.

No release commit, tag, release note, final-gate evidence, or V3.0.1 README history was
modified.

## Validation

| Validation | Result |
| --- | --- |
| Standard `python -m pytest` | Host `rlcompleter` / debugging-plugin segmentation fault reproduced; exit 139 |
| Approved host workaround | `python -m pytest -p no:debugging` — **414 passed** |
| Offline LLM-contract smoke | `python -m pytest -p no:debugging tests/test_llm_contracts.py` — **6 passed** |
| Core import smoke | PASS |

The import smoke covered `code_maintenance`, `credits`, `managed_access`,
`admin_operations`, `llm_provider`, `llm_service`, `processor`, and `config`.

All tests remained offline. No real API, Credential, Provider request, or network LLM
request was used. The known host issue requires no repository or UI/Gradio change.

## Product and Thesis Direction

V3.1.0 targets Project Intelligence / RAG: stronger full-project retrieval, context
construction, and project understanding. It should provide dependable project context
for the future V3.2 Controlled Multi-Agent Collaboration stage.

V3.1.0 is a thesis-core stage. Its architecture must support implementation plus
research questions, controlled baselines, quantitative evaluation, ablation, and
reproducibility. The evaluation-first rule is frozen: the architecture must state not
only how RAG will work, but how evidence will demonstrate whether it works.

## Questions Registered for Phase 0 Review

The following questions are registered but deliberately unanswered by Phase 0.0:

1. Which retrieval unit best fits code projects: file, symbol, chunk, or hybrid?
2. How do lexical, embedding, and graph-aware retrieval compare for maintenance tasks?
3. Does hybrid retrieval outperform a single retrieval strategy?
4. Can `ProjectGraph` or `ProjectSnapshot` improve retrieval quality?
5. Can `SnapshotDiff` avoid full index rebuilds after incremental project changes?
6. Does RAG context improve downstream maintenance-task correctness or relevance?

Phase 0 must define a retrieval benchmark or dataset, ground truth, baselines, metrics,
ablations, and a reproducible experiment procedure. Candidate metrics are Recall@K,
Precision@K, MRR, Hit Rate@K, nDCG@K, context relevance, task success, LLM answer
correctness, and token/context cost; none is selected by this gate.

## Architecture Questions and Boundaries

- **Retrieval units:** evaluate file, symbol, chunk, and hybrid units while reusing
  stable `SymbolId`, the scanner, graph, and snapshots.
- **Strategies:** evaluate lexical/BM25-like, embedding, graph-aware expansion, hybrid
  retrieval, and reranking without choosing an algorithm in Phase 0.0.
- **Storage:** determine whether a vector database is necessary. Compare in-memory,
  standard-library/local, FAISS-like, Chroma-like, and justified alternatives with
  reproducibility, comparability, deployability, and experimental control in mind.
- **Embedding:** Phase 0 must decide provider, local/remote execution, BYOK/Managed
  relationship, offline tests, cache, privacy, and determinism before implementation.
- **Graph:** existing `CONTAINS` and `IMPORTS` relations may inform retrieval or
  expansion. Any relation expansion requires its own architecture review and must not
  silently change the frozen graph contract.
- **Snapshot:** `ProjectSnapshot`, content hashes, and `SnapshotDiff` are priority
  candidates for index identity, incremental indexing, change detection, and cache
  invalidation.
- **AnalysisEngine:** remains deterministic analysis, not RAG, an Agent runtime, or a
  planner. RAG remains a separate layer.
- **Package name:** remains undecided until Phase 0 review; no RAG package is created.
- **Multi-Agent:** V3.2 is not started. V3.1 may define a future consumption interface
  but no Agent runtime, planner, collaboration, memory, or router.
- **Router:** V3.3 is not started; embedding/model selection does not introduce a
  multi-model router.
- **Commercial track:** V3.0.2 remains deferred/optional. Admin UI, Payment, Recharge,
  and Auth/RBAC remain outside V3.1.

No embedding SDK, vector database, BM25 library, tree-sitter, ANTLR, JavaParser, Agent
framework, or other dependency was installed. `requirements.txt` remains unchanged.

## Permanent Documentation Policies

Every formal version—major, minor, or patch—must have an accurate, concise README
Version History entry. Feature releases record Version, Status, Major Updates, Phase
Summary when needed, and Tests; patch releases record Version, Status, Changes/Fixes,
and Tests. Internal QA finding IDs, probe counts, and directed-retest workflow details
do not belong in README history.

After each formal release, create a version-level Thesis-Oriented Development Report
under `docs/thesis/` using `V<major>_<minor>_<patch>_Thesis_Development_Report.md`, for
example `V3_1_0_Thesis_Development_Report.md`. The report must
reorganize evidence from real code, Development Reports, QA Reports, and release
evidence into thesis-usable material rather than concatenate reports.

At this gate, neither V3.0.0 nor V3.0.1 has a tracked thesis report. V3.0.0 is a
Documentation Backlog item. A pre-existing untracked V3.0.1 candidate report is
preserved outside this commit and requires a separate Documentation Task before it can
become repository evidence. This backlog does not block V3.1.0.

## Process and Next Gate

Development continues through implementation, independent QA, necessary hardening,
directed retest, Development Report, QA Report, and Documentation Gate. Version
completion continues through Release Engineering, Repository Hygiene, Product
Documentation, Full-System QA, Final Review, Final Release Gate, tag/remote
publication, and the version-level Thesis Development Report.

The next allowed stage is **V3.1.0 Phase 0 Architecture & Research Review**. This gate
does not begin that review, answer its research questions, or implement any RAG,
embedding, vector database, Agent, or Router code.
