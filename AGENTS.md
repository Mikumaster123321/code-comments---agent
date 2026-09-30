# Shared AI Engineering Rules

These rules apply to Codex, Trae Work, Cursor, and any other engineering AI. Start every task by reading `PROJECT_CONTEXT.md`.

## Before Changing Anything

1. Check `git branch --show-current`, `git status --short`, and `git diff` / `git diff --cached`.
2. Read `PROJECT_CONTEXT.md` and the relevant existing code and tests.
3. Establish the baseline with `python -m pytest`.

Use the repository's real commands:

```bash
python -m pytest
python -m pytest tests/test_llm_contracts.py
python main.py
```

The targeted LLM-contract test is an offline smoke check: it stubs the LLM call. Do not make a real provider request when testing.

## Implementation Rules

- Make changes small, explicit, testable, and incremental.
- Reuse established logic and style; avoid needless comments, over-abstraction, and placeholder architecture.
- Preserve user changes. Never overwrite unrelated edits.
- Do not call real LLM APIs or use real API keys in tests. Do not delete a failing test merely to make the suite green.
- A strict xfail may be removed only after the underlying behavior is truly fixed and verified.
- Do not commit secrets.
- Do not substantially change `processor`, UI, or providers without approval.
- During V3.0, do not create `rag`, `agents`, `router`, `api`, or `vscode` modules and do not introduce tree-sitter, ANTLR, or JavaParser.

## Git Rules

- Do not force-push or rewrite history. Do not overwrite user work.
- Make each completed phase its own commit.
- Before handoff, report changed files, tests run, behavior changes, open problems, commit, and status.

## Model Collaboration Roles

- GPT-5.6 Sol controls the overall workflow, performs cross-phase audits, and keeps
  prompts, gates, thesis claims, and engineering evidence consistent.
- Codex performs repository implementation, testing, Git operations, and
  documentation materialization.
- DeepSeek R1 performs independent QA, directed retests, and adversarial
  verification. It must not overturn frozen architecture or methodology.
- Claude, using the highest available Opus model with high reasoning, is the
  preferred Primary Research Architecture & Methodology Reviewer. It reviews
  architecture and research design, RQs and experiment protocols, dataset and
  ground-truth methodology, and the methodological validity of research results.
- Grok 4.7 normally serves as the Independent Research Cross-Reviewer / Alternative
  Methodology Reviewer. It independently challenges Claude/GPT research designs and
  reviews dataset bias, leakage, threats to validity, negative results, and claim
  discipline.
- Grok 4.7 assumes Claude's Primary Research/Methodology Reviewer duties only when
  the user explicitly states that Claude is currently unavailable. This is a
  temporary fallback, not an automatic substitution. When Claude becomes available,
  the Primary role returns to Claude and Grok 4.7 returns to its normal independent
  cross-review role.
- The user makes final decisions and acceptance.

Formal prompts and execution reports should be written primarily in Simplified
Chinese; English technical terms may be retained where they improve precision. Any
important external-model decision that will determine code, formal experiment, or
release behavior must first be materialized in a Git-tracked specification or
decision document before a later phase may depend on it. Chat history alone is not a
repository Source of Truth.

If a tool does not automatically load these files, explicitly instruct it at task
start to read `AGENTS.md` and `PROJECT_CONTEXT.md`.
