# V3.1.4 Pre-V3.2 Compatibility Contract

Status: `FROZEN FOR V3.1.4 / PRE-V3.2`

This contract records existing, tested interfaces that V3.2 may reuse. It does not
create an Agent, Planner, Critic, Router, Memory, Tool, or Orchestrator API.

## Stability levels

- `STABLE`: downstream code may depend on the named import, identity, and documented
  value/shape semantics.
- `LEGACY-COMPAT`: the root or tuple surface remains callable for existing users, but
  its internal implementation may continue to evolve behind that surface.
- `INTERNAL`: repository implementation detail; no external compatibility promise.
- `EXPERIMENTAL / OPERATIONAL`: developer, experiment, or release operation with its
  separately documented evidence and lifecycle rules.
- `FROZEN-FORMAL`: research protocol/evidence surface that maintenance and V3.2 must
  not modify without a separately authorized research phase.

## STABLE

| Surface | Frozen contract |
|---|---|
| Provider registry IDs | `deepseek`, `openai`, `azure`, `dashscope`, `moonshot`, `custom`; existing default models remain unchanged |
| `llm_provider.ModelConfig` | immutable, credential-free `provider_id`, `model`, `base_url` value |
| `llm_provider.RuntimeCredential` | runtime-only, redacted, non-serializable credential wrapper |
| `llm_provider.TaskScopedLLMProvider` | captures one model/client pair for one request/task and exposes `create_completion` |
| `code_maintenance` public domain | `Project`, `ProjectDirectory`, `ProjectFile`, `SourceFile`, `Symbol`, `SymbolId`, `SymbolKind`, scan/snapshot/graph value types |
| `code_maintenance` adapters | `LanguageAdapter`, `PythonAdapter`, `JavaAdapter` |
| Project Intelligence facade | `RetrievalService`, `RetrievalQuery`, `ContextPackage` and their documented immutable domain values |
| Project representation | scanner/snapshot/domain identities used by `code_maintenance` and `project_intelligence` |

Stability protects imports, identities, and documented value semantics. It does not
freeze private attributes, construction shortcuts used only by tests, or a future
implementation strategy.

## LEGACY-COMPAT

| Surface | Compatibility promise |
|---|---|
| `processor.process_code()` | public five-item tuple remains `(annotated_code, markdown_doc, log_text, md_path, src_path)` |
| `processor.process_code_with_progress()` | intermediate and final five-item frame shape remains compatible |
| `processor.process_batch_files()` | public `(log_text, zip_path)` tuple remains compatible |
| `processor.process_batch_with_progress()` | `(log_text, zip_path)` frames remain compatible |
| `processor.CancelToken` | `cancel()`, `reset()`, and `is_canceled()` remain available; cancellation is cooperative |
| root workspace helpers | `processor.save_workspace`, `load_workspace`, `clear_workspace`, and existing helper re-exports remain available |
| `ui.CUSTOM_CSS` | root re-export remains available |
| legacy `config` globals | dynamic `client`, `MODEL`, and price globals remain readable through the current compatibility layer |

The batch implementation may use typed internal outcomes. Those outcomes are not
added to the public tuple. Safety rejections, no credential crossover, conservative
request attempts, accurate all-failed classification, and `Cancelled` rather than
`Idle` are intentional V3.1.4 behavior changes inside the compatible shapes.

## INTERNAL

- `code_comments_agent.reliability`, resource limits, diagnostic allow-list, batch
  outcome classification, client construction helpers, and executor shutdown details;
- Provider active-state globals and locking implementation;
- temporary staging layouts and intermediate download filenames;
- individual UI callbacks and Gradio component wiring;
- parser/annotator helper functions not exported by the public packages.

Internal status does not permit credential leakage, source/prompt logging, silent
workspace field loss, or changes to a `STABLE`/`LEGACY-COMPAT` surface.

## EXPERIMENTAL / OPERATIONAL

- `scripts/dev.py` doctor, smoke, test-profile, archive-validation, and release-check
  operations;
- optional local E5 runtime loading and resource probes;
- release schema v2 operational state, including the C1/tag/C2 flow and runtime-derived
  final HEAD;
- development/QA reports and benchmark runners within their documented authority.

These operations remain offline/read-only by default. Their evidence is not a general
production SLA or public library API guarantee.

## FROZEN-FORMAL

The following are outside V3.1.4 and ordinary V3.2 implementation authority:

- BM25/E5 fingerprints and frozen model revision;
- Graph expansion semantics;
- Hybrid Weighted/RRF ranking and configuration;
- `ContextBuilder` budget and ordering semantics;
- experiment schemas, Dataset/Query/Ground Truth/Grade, protocols and amendments;
- Formal artifact contents, metrics, result interpretation, and identities.

Frozen identity:

- execution revision:
  `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- artifact-set identity:
  `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- artifact-set SHA-256:
  `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`

## Current deployment boundary

The supported product threat model is a localhost, single-user, desktop-style
application. Process-global Provider settings and one OS-user workspace are acceptable
inside that model. They are not a multi-tenant isolation claim. V3.2 must make an
explicit architectural decision before using these globals in any different threat
model.
