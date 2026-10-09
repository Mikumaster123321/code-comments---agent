# Documentation Navigation

Current state: V3.1.4 `IMPLEMENTATION COMPLETE / AWAITING FINAL QA`.

## Current authorities

- [V3.1.4 Scope Freeze](development/V3_1_4_Reliability_Stabilization_Scope.md)
- [Runtime and Reliability Contract](architecture/V3_1_4_Runtime_Reliability_Contract.md)
- [Pre-V3.2 Compatibility Contract](architecture/V3_1_4_Pre_V3_2_Compatibility_Contract.md)
- [Development Report](development/Development_Report_V3_1_4.md)
- [Development documentation index](development/README.md)
- [QA documentation index](qa/README.md)
- [Release documentation and machine-readable state](release/README.md)
- [Permanent Version Documentation Contract](release/Version_Documentation_Contract.md)
- [Root current project context](../PROJECT_CONTEXT.md)

Current machine state is determined by Git objects plus
`release/release_state.json`. Human current summaries are the root README, root
`PROJECT_CONTEXT.md`, and `release/README.md`. Versioned scope, thesis, report, release
notes, and QA files are time-point evidence.

## Protected and frozen areas

- `docs/experiments/` — **FROZEN FORMAL EVIDENCE**; V3.1.4 does not modify its
  protocols, datasets, artifacts, CSVs, results, or interpretation.
- `docs/thesis/` — **USER-PROTECTED PATH / DO NOT TOUCH**.

V3.1.4 Final QA is not yet executed. The expected future evidence path is
`qa/V3_1_4_Final_Release_QA.md`; no placeholder PASS exists.
