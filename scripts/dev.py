#!/usr/bin/env python3
"""Unified, read-only-by-default developer workflow commands for V3.1.3."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

BASELINE_VERSION = "3.1.2"
BASELINE_RELEASE_COMMIT = "247bbfc1f849b929a00b32b09ada5e060ceef9d9"
BASELINE_TAG = "v3.1.2"
FORMAL_EXECUTION_REVISION = "2749969cd3a2d4d6e1e8d81160eebd5fb360879b"
FORMAL_ARCHIVE_COMMIT = "c3ee6ec1b7aa28c2539d2fe849d1f25268807677"
FORMAL_ARTIFACT_PATH = (
    "docs/experiments/audits/phase64_formal_english_test/artifact_set.json"
)
FORMAL_ARTIFACT_IDENTITY = (
    "acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3"
)
FORMAL_ARTIFACT_SHA256 = (
    "2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41"
)
PROTECTED_PATH = "docs/thesis/"
RELEASE_STATE_PATH = "docs/release/release_state.json"
REQUIRED_RELEASE_REMOTES = ("github", "gitee")
RELEASE_LIFECYCLE_STATES = {"PREPARING", "RELEASE_CANDIDATE", "RELEASED"}
RELEASE_STATE_V1_FIELDS = {
    "schema_version",
    "version",
    "state",
    "expected_branch",
    "release_commit",
    "tag",
    "baseline",
    "document_sentinel",
    "required_documents",
}
RELEASE_STATE_V2_FIELDS = {
    "schema_version",
    "version",
    "state",
    "expected_development_branch",
    "expected_main_branch",
    "release_commit",
    "tag",
    "baseline",
    "required_documents",
    "final_qa_evidence",
}

E5_REPOSITORY = "intfloat/multilingual-e5-base"
E5_REVISION = "d128750597153bb5987e10b1c3493a34e5a4502a"
E5_DIMENSION = 768
E5_DEPENDENCIES = {
    "torch": "2.8.0",
    "transformers": "4.56.2",
    "safetensors": "0.6.2",
}
E5_REQUIRED_FILES = (
    "config.json",
    "model.safetensors",
    "sentencepiece.bpe.model",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
)

CORE_DEPENDENCIES = ("openai", "gradio", "python-dotenv", "pytest")
REPORTED_ENVIRONMENT_VARIABLES = (
    "HF_HOME",
    "HF_HUB_CACHE",
    "TRANSFORMERS_CACHE",
    "HF_HUB_OFFLINE",
    "TRANSFORMERS_OFFLINE",
    "OPENAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "DASHSCOPE_API_KEY",
    "MOONSHOT_API_KEY",
)

TEST_PROFILES: dict[str, tuple[str, ...]] = {
    "llm": ("tests/test_llm_contracts.py",),
    "production": (
        "tests/test_project_graph.py",
        "tests/test_project_intelligence_corpus.py",
        "tests/test_project_intelligence_lexical.py",
        "tests/test_project_intelligence_embedding.py",
        "tests/test_project_intelligence_local_embedding.py",
        "tests/test_project_intelligence_graph_expansion.py",
        "tests/test_project_intelligence_index.py",
        "tests/test_project_intelligence_hybrid.py",
        "tests/test_project_intelligence_context.py",
        "tests/test_project_intelligence_service.py",
        "tests/test_experiment_production_execution.py",
    ),
    "experiments": (
        "tests/test_experiment_benchmark_infrastructure.py",
        "tests/test_experiment_production_execution.py",
        "tests/test_experiment_serialization_security.py",
        "tests/test_experiment_reference_lifecycle.py",
        "tests/test_project_intelligence_context.py",
    ),
    "full": (),
    "release": (
        "tests/test_release_workflow.py",
        "tests/test_repository_architecture.py",
    ),
}


@dataclass(frozen=True)
class WorkflowError(Exception):
    what: str
    expected: str
    actual: str
    recovery: str


def _fail(what: str, expected: object, actual: object, recovery: str) -> None:
    raise WorkflowError(what, str(expected), str(actual), recovery)


def _require(
    condition: bool,
    what: str,
    expected: object,
    actual: object,
    recovery: str,
) -> None:
    if not condition:
        _fail(what, expected, actual, recovery)


def _print_failure(error: WorkflowError) -> None:
    print(f"What failed: {error.what}", file=sys.stderr)
    print(f"Expected: {error.expected}", file=sys.stderr)
    print(f"Actual: {error.actual}", file=sys.stderr)
    print(f"Safe recovery: {error.recovery}", file=sys.stderr)


def _run_process(
    command: Sequence[str],
    *,
    root: Path = REPOSITORY_ROOT,
    capture: bool = False,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            cwd=root,
            check=False,
            capture_output=capture,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        _fail(
            "subprocess execution",
            "the requested executable completes within the diagnostic timeout",
            type(error).__name__,
            "verify the executable is installed and rerun the command",
        )


def _git(
    arguments: Sequence[str],
    *,
    root: Path = REPOSITORY_ROOT,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    return _run_process(["git", "-C", str(root), *arguments], root=root, capture=capture)


def _git_output(arguments: Sequence[str], *, root: Path = REPOSITORY_ROOT) -> str:
    result = _git(arguments, root=root)
    _require(
        result.returncode == 0,
        "Git read operation",
        "exit code 0",
        f"exit code {result.returncode}",
        "verify this is a readable Git repository and that Git is installed",
    )
    return result.stdout.strip()


def _dependency_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _pytest_probe(root: Path = REPOSITORY_ROOT) -> subprocess.CompletedProcess[str]:
    return _run_process(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "tests/test_llm_contracts.py",
        ],
        root=root,
        capture=True,
        timeout=30,
    )


def doctor(*, root: Path = REPOSITORY_ROOT) -> int:
    print("Developer environment doctor")
    print(f"repository_root={root}")
    print(f"python_executable={sys.executable}")
    print(f"python_version={platform.python_version()}")
    print(f"python_implementation={platform.python_implementation()}")
    print(f"platform={platform.platform()}")

    missing_core: list[str] = []
    print("core_runtime:")
    for dependency in CORE_DEPENDENCIES:
        version = _dependency_version(dependency)
        print(f"  {dependency}={version if version is not None else 'MISSING'}")
        if version is None:
            missing_core.append(dependency)

    print("optional_e5_runtime:")
    for dependency, expected in E5_DEPENDENCIES.items():
        version = _dependency_version(dependency)
        status = "MISSING" if version is None else version
        print(f"  {dependency}={status} (historical_formal={expected})")
    print(
        "historical_formal_runtime=CPython 3.12.14; torch 2.8.0; "
        "transformers 4.56.2; CPU float32 (metadata only)"
    )

    git_version = _run_process(["git", "--version"], root=root, capture=True)
    git_available = git_version.returncode == 0
    print(
        "git="
        + (git_version.stdout.strip() if git_available else f"UNAVAILABLE ({git_version.returncode})")
    )
    if git_available:
        branch = _git_output(["branch", "--show-current"], root=root)
        head = _git_output(["rev-parse", "HEAD"], root=root)
        print(f"branch={branch or '(detached)'}")
        print(f"head={head}")

    print("environment_variables:")
    for name in REPORTED_ENVIRONMENT_VARIABLES:
        print(f"  {name}={'set' if name in os.environ else 'unset'}")

    probe = _pytest_probe(root)
    if probe.returncode == 0:
        print("pytest_plugin_probe=PASS")
    else:
        print(f"pytest_plugin_probe=FAIL (exit_code={probe.returncode})", file=sys.stderr)
        print(
            "Safe recovery: run tests with 'python -m pytest -p no:debugging'; "
            "this is an observed environment workaround and does not change test semantics.",
            file=sys.stderr,
        )

    if missing_core or not git_available:
        print(
            "What failed: core developer runtime\n"
            f"Expected: installed core dependencies and Git\n"
            f"Actual: missing={missing_core}, git_available={git_available}\n"
            "Safe recovery: create the documented virtual environment and install requirements.txt",
            file=sys.stderr,
        )
        return 1
    return 0


def project_smoke() -> int:
    from code_maintenance import ProjectScanner, SnapshotBuilder
    from project_intelligence import BM25Index, CorpusBuilder, RetrievalQuery

    with tempfile.TemporaryDirectory(prefix="v311-project-smoke-") as temporary:
        root = Path(temporary)
        (root / "sample.py").write_text(
            "def account_balance(account):\n    return account.balance\n",
            encoding="utf-8",
        )
        scanner = ProjectScanner()
        snapshot = SnapshotBuilder().build(scanner.scan(root))
        corpus = CorpusBuilder(scanner=scanner).build(root, snapshot)
        index = BM25Index(corpus)
        hits = index.search("account balance", top_k=3)
        query = RetrievalQuery("account balance", top_k=3, context_budget=512)
        _require(
            snapshot.metadata.file_count == 1 and bool(corpus) and bool(hits),
            "Project Intelligence smoke",
            "one scanned file, a non-empty symbol corpus, and lexical hits",
            (
                f"files={snapshot.metadata.file_count}, documents={len(corpus)}, "
                f"hits={len(hits)}"
            ),
            "verify the scanner, language adapters, snapshot, corpus, and lexical index",
        )
        print("project_smoke=PASS")
        print(f"files={snapshot.metadata.file_count}")
        print(f"symbols={snapshot.metadata.symbol_count}")
        print(f"documents={len(corpus)}")
        print(f"hits={len(hits)}")
        print(f"query_top_k={query.top_k}")
    return 0


def _pytest_command(
    profile: str,
    passthrough: Sequence[str],
    *,
    root: Path = REPOSITORY_ROOT,
) -> list[str]:
    _require(
        profile in TEST_PROFILES,
        "test profile",
        ", ".join(TEST_PROFILES),
        profile,
        "choose one of the documented test profiles",
    )
    command = [sys.executable, "-m", "pytest"]
    probe = _pytest_probe(root)
    if probe.returncode != 0:
        command.extend(("-p", "no:debugging"))
        print(
            f"pytest plugin probe failed with exit code {probe.returncode}; "
            "applying the environment-only '-p no:debugging' workaround",
            file=sys.stderr,
        )
    command.extend(TEST_PROFILES[profile])
    command.extend(passthrough)
    return command


def run_test_profile(
    profile: str,
    passthrough: Sequence[str],
    *,
    root: Path = REPOSITORY_ROOT,
) -> int:
    result = _run_process(_pytest_command(profile, passthrough, root=root), root=root)
    if result.returncode != 0 or profile != "release":
        return result.returncode
    validate_archive_v310(root=root)
    metadata = _load_release_state(root)
    if metadata["state"] == "RELEASED":
        return release_check(str(metadata["version"]), remote=False, root=root)
    print("release_profile=PASS")
    print("release_gate=NOT_EXECUTED_AWAITING_FINAL_QA")
    return 0


def _candidate_cache_roots(explicit: Path | None) -> tuple[Path, ...]:
    if explicit is not None:
        return (explicit.expanduser().resolve(),)
    candidates: list[Path] = []
    if os.environ.get("HF_HUB_CACHE"):
        candidates.append(Path(os.environ["HF_HUB_CACHE"]).expanduser().resolve())
    if os.environ.get("TRANSFORMERS_CACHE"):
        candidates.append(Path(os.environ["TRANSFORMERS_CACHE"]).expanduser().resolve())
    if os.environ.get("HF_HOME"):
        candidates.append((Path(os.environ["HF_HOME"]).expanduser() / "hub").resolve())
    candidates.append((Path.home() / ".cache" / "huggingface" / "hub").resolve())
    return tuple(dict.fromkeys(candidates))


def _snapshot_from_cache(cache_root: Path) -> Path:
    encoded = "models--" + E5_REPOSITORY.replace("/", "--")
    candidates = (
        cache_root / encoded / "snapshots" / E5_REVISION,
        cache_root / "hub" / encoded / "snapshots" / E5_REVISION,
    )
    return next((path for path in candidates if path.is_dir()), candidates[0])


def _inside_repository(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _validate_model_snapshot(snapshot: Path, *, root: Path) -> None:
    _require(
        snapshot.is_dir(),
        "E5 snapshot availability",
        f"an existing local snapshot for revision {E5_REVISION}",
        str(snapshot),
        "provide --model-path or --cache-dir pointing to an existing frozen snapshot",
    )
    _require(
        not _inside_repository(snapshot, root),
        "E5 cache location",
        "a cache outside the repository tree",
        str(snapshot),
        "move the model cache outside the repository and rerun model-check",
    )
    dangling = [
        path.relative_to(snapshot).as_posix()
        for path in snapshot.rglob("*")
        if path.is_symlink() and not path.exists()
    ]
    _require(
        not dangling,
        "E5 snapshot symlinks",
        "no dangling symlinks",
        f"dangling={dangling}",
        "restore the missing cache blobs for the exact frozen revision",
    )
    config_path = snapshot / "config.json"
    missing = [name for name in E5_REQUIRED_FILES if not (snapshot / name).is_file()]
    _require(
        not missing,
        "E5 snapshot files",
        ", ".join(E5_REQUIRED_FILES),
        f"missing={missing}",
        "restore the exact frozen snapshot without overwriting repository files",
    )
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(
            "E5 model metadata",
            "valid UTF-8 config.json",
            type(error).__name__,
            "restore config.json from the exact frozen snapshot",
        )
    resolved_revision = snapshot.name
    _require(
        resolved_revision == E5_REVISION,
        "E5 resolved revision",
        E5_REVISION,
        resolved_revision,
        "select the snapshot directory named by the frozen commit",
    )
    encoded_repository = "models--" + E5_REPOSITORY.replace("/", "--")
    configured_repository = config.get("_name_or_path")
    repository_matches = encoded_repository in snapshot.parts or configured_repository == E5_REPOSITORY
    _require(
        repository_matches,
        "E5 repository identity",
        E5_REPOSITORY,
        configured_repository or "not encoded by snapshot path/config",
        "select the frozen intfloat/multilingual-e5-base cache snapshot",
    )
    hidden_size = config.get("hidden_size")
    _require(
        hidden_size == E5_DIMENSION,
        "E5 hidden dimension",
        E5_DIMENSION,
        hidden_size,
        "restore model metadata from the frozen revision",
    )


def _model_smoke(snapshot: Path) -> None:
    from project_intelligence import LocalE5EmbeddingProvider

    provider = LocalE5EmbeddingProvider(
        model_path=snapshot,
        local_files_only=True,
        device="cpu",
        batch_size=1,
    )
    query = provider.embed_query("locate account balance")
    document = provider.embed_documents(("def account_balance(account): return account.balance",))[0]
    for name, vector in (("query", query), ("document", document)):
        values = vector.values
        norm = math.sqrt(math.fsum(value * value for value in values))
        _require(
            len(values) == E5_DIMENSION and all(math.isfinite(value) for value in values),
            f"E5 {name} vector",
            f"{E5_DIMENSION} finite values",
            f"dimension={len(values)}",
            "verify the frozen model files and pinned optional dependencies",
        )
        _require(
            abs(norm - 1.0) < 1e-5,
            f"E5 {name} normalization",
            "L2 norm within 1e-5 of 1.0",
            norm,
            "verify CPU float32 inference through the unchanged local provider",
        )


def model_check(
    *,
    cache_dir: Path | None,
    model_path: Path | None,
    smoke: bool,
    root: Path = REPOSITORY_ROOT,
) -> int:
    actual_dependencies = {name: _dependency_version(name) for name in E5_DEPENDENCIES}
    mismatches = {
        name: actual_dependencies[name]
        for name, expected in E5_DEPENDENCIES.items()
        if actual_dependencies[name] != expected
    }
    _require(
        not mismatches,
        "optional E5 dependencies",
        E5_DEPENDENCIES,
        actual_dependencies,
        "install requirements-embedding.txt in an isolated optional environment",
    )
    if model_path is not None:
        snapshot = model_path.expanduser().resolve()
    else:
        roots = _candidate_cache_roots(cache_dir)
        snapshots = tuple(_snapshot_from_cache(path) for path in roots)
        snapshot = next((path for path in snapshots if path.is_dir()), snapshots[0])
    _validate_model_snapshot(snapshot, root=root)
    print("model_check=PASS")
    print(f"repository={E5_REPOSITORY}")
    print(f"revision={E5_REVISION}")
    print(f"dimension={E5_DIMENSION}")
    print(f"snapshot={snapshot}")
    print("network=disabled")
    if smoke:
        _model_smoke(snapshot)
        print("lightweight_smoke=PASS")
    else:
        print("lightweight_smoke=NOT_REQUESTED")
    return 0


def _read_committed_json(authority, path: str) -> dict:
    value = authority.json_record(path)
    return dict(value)


def _verify_ancestor(root: Path, ancestor: str, descendant: str, label: str) -> None:
    result = _git(["merge-base", "--is-ancestor", ancestor, descendant], root=root)
    _require(
        result.returncode == 0,
        label,
        f"{ancestor} is an ancestor of {descendant}",
        f"git exit code {result.returncode}",
        "restore the released Git ancestry; do not reset or rewrite history automatically",
    )


def validate_archive_v310(*, root: Path = REPOSITORY_ROOT) -> int:
    from experiments import DryRunReceiptV2, RepositoryAuthority, canonical_hash
    from experiments.config import FROZEN_MATRIX_IDS

    authority = RepositoryAuthority(root)
    raw = authority.raw_bytes(FORMAL_ARTIFACT_PATH)
    actual_sha = hashlib.sha256(raw).hexdigest()
    _require(
        actual_sha == FORMAL_ARTIFACT_SHA256,
        "V3.1.0 Formal artifact-set file SHA-256",
        FORMAL_ARTIFACT_SHA256,
        actual_sha,
        "restore the released artifact from v3.1.0; do not regenerate it",
    )
    artifact = json.loads(raw)
    actual_identity = canonical_hash(artifact)
    _require(
        actual_identity == FORMAL_ARTIFACT_IDENTITY,
        "V3.1.0 Formal artifact-set canonical identity",
        FORMAL_ARTIFACT_IDENTITY,
        actual_identity,
        "restore the released artifact from v3.1.0; do not rerun Formal",
    )
    expected_scope = (
        FORMAL_EXECUTION_REVISION,
        "formal",
        17,
        48,
        816,
        tuple(FROZEN_MATRIX_IDS),
    )
    actual_scope = (
        artifact.get("execution_revision"),
        artifact.get("mode"),
        artifact.get("config_count"),
        artifact.get("query_count"),
        artifact.get("query_config_pair_count"),
        tuple(artifact.get("matrix_ids", ())),
    )
    _require(
        actual_scope == expected_scope,
        "V3.1.0 Formal archive scope",
        expected_scope,
        actual_scope,
        "restore the frozen artifact set and matrix; do not edit its scope",
    )
    runs = artifact.get("runs")
    _require(
        isinstance(runs, list) and len(runs) == 17,
        "V3.1.0 Formal run catalog",
        "17 run records",
        type(runs).__name__ if not isinstance(runs, list) else len(runs),
        "restore the released artifact-set run catalog",
    )
    for run in runs:
        for path_key, digest_key in (
            ("manifest_path", "manifest_sha256"),
            ("aggregate_path", "aggregate_sha256"),
            ("raw_path", "raw_sha256"),
            ("authority_binding_path", "authority_binding_sha256"),
        ):
            actual = authority.raw_checksum(run[path_key])
            _require(
                actual == run[digest_key],
                f"Formal run checksum: {run['matrix_run_id']} {path_key}",
                run[digest_key],
                actual,
                "restore the released run artifact; do not regenerate it",
            )
        if run.get("context_diagnostic_path") is not None:
            actual = authority.raw_checksum(run["context_diagnostic_path"])
            _require(
                actual == run["context_diagnostic_sha256"],
                f"Formal context diagnostic checksum: {run['matrix_run_id']}",
                run["context_diagnostic_sha256"],
                actual,
                "restore the released context diagnostic artifact",
            )
        manifest = _read_committed_json(authority, run["manifest_path"])
        aggregate = _read_committed_json(authority, run["aggregate_path"])
        raw_rows = [
            json.loads(line)
            for line in authority.raw_bytes(run["raw_path"]).decode("utf-8").splitlines()
        ]
        actual_run_scope = (
            manifest.get("execution_revision"),
            manifest.get("mode"),
            manifest.get("split"),
            aggregate.get("run_status"),
            aggregate.get("denominator_count"),
            len(raw_rows),
            {row.get("status") for row in raw_rows},
            {row.get("matrix_run_id") for row in raw_rows},
        )
        expected_run_scope = (
            FORMAL_EXECUTION_REVISION,
            "formal",
            "english_test",
            "success",
            48,
            48,
            {"success"},
            {run["matrix_run_id"]},
        )
        _require(
            actual_run_scope == expected_run_scope,
            f"Formal run scope: {run['matrix_run_id']}",
            expected_run_scope,
            actual_run_scope,
            "restore the released run artifacts; do not execute a replacement run",
        )

    for path_key, digest_key in (
        ("determinism_evidence_path", "determinism_evidence_sha256"),
        ("leakage_evidence_path", "leakage_evidence_sha256"),
    ):
        actual = authority.raw_checksum(artifact[path_key])
        _require(
            actual == artifact[digest_key],
            f"Formal evidence checksum: {path_key}",
            artifact[digest_key],
            actual,
            "restore the released evidence artifact",
        )
    authority.load_typed(
        artifact["dry_run_receipt_path"],
        DryRunReceiptV2,
        artifact["dry_run_receipt_identity"],
    )
    _verify_ancestor(root, FORMAL_EXECUTION_REVISION, FORMAL_ARCHIVE_COMMIT, "Formal archive ancestry")
    head = _git_output(["rev-parse", "HEAD"], root=root)
    _verify_ancestor(root, FORMAL_ARCHIVE_COMMIT, head, "Release/archive ancestry")
    artifact_diff = _git(
        [
            "diff",
            "--quiet",
            FORMAL_ARCHIVE_COMMIT,
            "HEAD",
            "--",
            "docs/experiments/formal_runs",
            "docs/experiments/audits/phase64_formal_english_test",
        ],
        root=root,
    )
    _require(
        artifact_diff.returncode == 0,
        "Formal protected artifact immutability",
        "no changes since the Formal archive commit",
        f"git diff exit code {artifact_diff.returncode}",
        "restore the released Formal artifact paths; do not rewrite them",
    )
    csv_check = _run_process(
        [sys.executable, str(root / "scripts/export_formal_thesis_tables.py"), "--check"],
        root=root,
        capture=True,
    )
    _require(
        csv_check.returncode == 0,
        "Formal CSV deterministic export",
        "exit code 0",
        f"exit code {csv_check.returncode}",
        "inspect the explicit export validation error and restore released CSV/artifact bytes",
    )
    print("archive_v3.1.0=PASS")
    print(f"formal_execution_revision={FORMAL_EXECUTION_REVISION}")
    print(f"formal_archive_commit={FORMAL_ARCHIVE_COMMIT}")
    print(f"artifact_identity={actual_identity}")
    print(f"artifact_sha256={actual_sha}")
    print("formal_scope=17 configs; 48 English Test queries; 816 query-config pairs")
    return 0


ELIGIBILITY_RECOVERY = {
    "repository_not_found": "run the command against the repository root",
    "artifact_missing": "restore the committed authority artifact",
    "artifact_not_committed": "commit the reviewed authority artifact before preflight",
    "artifact_worktree_mismatch": "restore committed bytes or review and commit the intended change",
    "current_gate_conflict": "inspect the committed current gate and selected approval",
    "frozen_commit_unavailable": "restore the complete Git history containing frozen revisions",
}


def experiment_preflight(purpose: str, *, root: Path = REPOSITORY_ROOT) -> int:
    from experiments import (
        DryRunReceiptV2,
        EligibilityError,
        RepositoryAuthority,
    )
    from experiments.eligibility import validate_current_gate

    try:
        authority = RepositoryAuthority(root)
        authority.verify_frozen_checksums()
        gate = authority.load_current_gate()
        validate_current_gate(authority, gate)
        artifact = authority.json_record(FORMAL_ARTIFACT_PATH)
        if purpose == "formal":
            receipt_path = artifact.get("dry_run_receipt_path")
            receipt_identity = artifact.get("dry_run_receipt_identity")
            _require(
                isinstance(receipt_path, str) and isinstance(receipt_identity, str),
                "Formal preflight receipt reference",
                "a frozen receipt path and identity",
                f"path={receipt_path!r}, identity={receipt_identity!r}",
                "restore the released Formal artifact set",
            )
            receipt = authority.load_typed(receipt_path, DryRunReceiptV2, receipt_identity)
            receipt_archive = authority.artifact_archive_commit(receipt_path)
            _verify_ancestor(
                root,
                receipt.execution_revision,
                receipt_archive,
                "Dry Run execution/archive ancestry",
            )
        print(f"experiment_preflight={purpose}:PASS")
        print(f"current_gate={gate.current_gate}")
        print(f"phase_status={gate.phase_status}")
        print("scope=committed repository authority only")
        print("runtime_and_requested_config=NOT_EVALUATED")
        return 0
    except EligibilityError as error:
        code = str(error)
        raise WorkflowError(
            f"experiment authority preflight ({code})",
            "existing committed validators accept the frozen authority",
            code,
            ELIGIBILITY_RECOVERY.get(
                code,
                "inspect the named stable failure code and restore its committed prerequisite",
            ),
        ) from None


def _load_release_state(root: Path) -> dict:
    path = root / RELEASE_STATE_PATH
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(
            "release state metadata",
            f"valid UTF-8 JSON at {RELEASE_STATE_PATH}",
            type(error).__name__,
            "create or restore the reviewed machine-readable release state",
        )
    schema_version = state.get("schema_version") if isinstance(state, dict) else None
    required = {
        "v1": RELEASE_STATE_V1_FIELDS,
        "v2": RELEASE_STATE_V2_FIELDS,
    }.get(schema_version)
    _require(
        required is not None and set(state) == required,
        "release state schema",
        "the exact v1 legacy or v2 two-stage release schema",
        sorted(state) if isinstance(state, dict) else type(state).__name__,
        "restore release_state.json with the documented minimal schema",
    )
    _require(
        state["state"] in RELEASE_LIFECYCLE_STATES,
        "release state value",
        "PREPARING, RELEASE_CANDIDATE, or RELEASED",
        f"schema={state['schema_version']!r}, state={state['state']!r}",
        "set an explicit reviewed release lifecycle state",
    )
    required_documents = state["required_documents"]
    _require(
        isinstance(required_documents, list)
        and bool(required_documents)
        and all(isinstance(path, str) and path for path in required_documents),
        "release document metadata",
        "a non-empty path list",
        required_documents,
        "restore the reviewed release document inventory",
    )
    if schema_version == "v1":
        _require(
            isinstance(state["expected_branch"], str)
            and bool(state["expected_branch"])
            and isinstance(state["document_sentinel"], str)
            and bool(state["document_sentinel"]),
            "legacy release intent",
            "a branch and document sentinel",
            {
                "expected_branch": state["expected_branch"],
                "document_sentinel": state["document_sentinel"],
            },
            "restore the published v1 release intent",
        )
    else:
        final_qa_evidence = state["final_qa_evidence"]
        _require(
            all(
                isinstance(state[field], str) and bool(state[field])
                for field in (
                    "expected_development_branch",
                    "expected_main_branch",
                    "final_qa_evidence",
                )
            )
            and final_qa_evidence.startswith("docs/qa/")
            and final_qa_evidence in required_documents,
            "two-stage release intent",
            "development/main branches and a required docs/qa Final QA evidence path",
            {
                "expected_development_branch": state["expected_development_branch"],
                "expected_main_branch": state["expected_main_branch"],
                "final_qa_evidence": final_qa_evidence,
            },
            "restore the stable v2 release intent without recording a dynamic final HEAD",
        )
    return state


def _read_code_version(root: Path) -> str:
    content = (root / "code_maintenance/__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"\s*$', content, re.MULTILINE)
    _require(
        match is not None,
        "project version metadata",
        "one literal code_maintenance.__version__ assignment",
        "missing or non-literal assignment",
        "restore the stable project version declaration",
    )
    return match.group(1)


def _release_worktree_check(root: Path) -> None:
    status = _git_output(["status", "--porcelain=v1"], root=root)
    status_rows = tuple(line for line in status.splitlines() if line)
    protected_staged = tuple(
        line[3:]
        for line in status_rows
        if line[:2] != "??"
        and (
            line[3:] == PROTECTED_PATH.rstrip("/")
            or line[3:].startswith(PROTECTED_PATH)
        )
    )
    _require(
        not protected_staged,
        "protected path staging",
        f"no staged paths under {PROTECTED_PATH}",
        protected_staged,
        "unstage the protected user path without reading or modifying it",
    )
    blocking: list[str] = []
    for line in status_rows:
        path = line[3:]
        if line.startswith("?? ") and (
            path == PROTECTED_PATH.rstrip("/") or path.startswith(PROTECTED_PATH)
        ):
            continue
        blocking.append(line)
    _require(
        not blocking,
        "release working tree",
        "no tracked/staged changes and only the allowed protected untracked path",
        blocking,
        "commit reviewed release files and leave unrelated user files untouched",
    )


def _verify_tag_state(version: str, state: dict, root: Path) -> None:
    tag_name = f"v{version}"
    tag_exists = _git(["rev-parse", "--verify", "--quiet", f"refs/tags/{tag_name}"], root=root)
    if state["state"] == "RELEASED":
        _require(
            state["tag"] == tag_name and isinstance(state["release_commit"], str),
            "released tag metadata",
            f"tag={tag_name} and a release commit",
            f"tag={state['tag']!r}, commit={state['release_commit']!r}",
            "record the reviewed release commit and tag",
        )
        _require(
            tag_exists.returncode == 0,
            "released local tag",
            tag_name,
            "missing",
            "create the annotated tag only in the separately authorized release step",
        )
        target = _git_output(["rev-parse", f"{tag_name}^{{}}"], root=root)
        _require(
            target == state["release_commit"],
            "released tag target",
            state["release_commit"],
            target,
            "do not overwrite the tag; investigate the release history",
        )
        head = _git_output(["rev-parse", "HEAD"], root=root)
        ancestor = _git(
            ["merge-base", "--is-ancestor", state["release_commit"], head],
            root=root,
        )
        _require(
            ancestor.returncode == 0,
            "release commit ancestry",
            f"{state['release_commit']} is an ancestor of runtime HEAD {head}",
            f"git merge-base --is-ancestor exit code {ancestor.returncode}",
            "do not rewrite the tag or history; restore a descendant release-record HEAD",
        )
    else:
        _require(
            state["tag"] is None and state["release_commit"] is None,
            "pre-release tag metadata",
            "null tag and release_commit",
            f"tag={state['tag']!r}, commit={state['release_commit']!r}",
            "keep tag/commit null until the authorized release step",
        )
        _require(
            tag_exists.returncode != 0,
            "pre-release local tag state",
            f"no {tag_name} tag",
            "tag already exists",
            "stop and inspect the unexpected tag; never overwrite it automatically",
        )


def _remote_tag_check(version: str, state: dict, root: Path) -> None:
    remotes = tuple(line for line in _git_output(["remote"], root=root).splitlines() if line)
    _require(
        bool(remotes),
        "release remote discovery",
        "at least one configured remote",
        "none",
        "configure the intended read-only release remotes",
    )
    tag_name = f"v{version}"
    for remote in remotes:
        result = _git(
            [
                "ls-remote",
                "--tags",
                remote,
                f"refs/tags/{tag_name}",
                f"refs/tags/{tag_name}^{{}}",
            ],
            root=root,
        )
        _require(
            result.returncode == 0,
            f"remote tag read: {remote}",
            "git ls-remote exit code 0",
            f"exit code {result.returncode}",
            "restore read-only remote connectivity and rerun with --remote",
        )
        lines = tuple(line for line in result.stdout.splitlines() if line)
        if state["state"] == "RELEASED":
            peeled = next((line.split()[0] for line in lines if line.endswith("^{}")), None)
            _require(
                peeled == state["release_commit"],
                f"remote released tag target: {remote}",
                state["release_commit"],
                peeled or "missing",
                "do not push or overwrite automatically; inspect remote release state",
            )
        else:
            _require(
                not lines,
                f"remote pre-release tag state: {remote}",
                f"no {tag_name} tag",
                lines,
                "stop and inspect the unexpected remote tag",
            )


def _remote_release_check(version: str, state: dict, root: Path, head: str) -> None:
    remotes = tuple(line for line in _git_output(["remote"], root=root).splitlines() if line)
    missing_remotes = tuple(remote for remote in REQUIRED_RELEASE_REMOTES if remote not in remotes)
    _require(
        not missing_remotes,
        "release remote discovery",
        REQUIRED_RELEASE_REMOTES,
        remotes,
        "configure the reviewed GitHub and Gitee remotes before remote verification",
    )
    tag_name = f"v{version}"
    main_branch = state["expected_main_branch"]
    development_branch = state["expected_development_branch"]
    for remote in REQUIRED_RELEASE_REMOTES:
        result = _git(
            [
                "ls-remote",
                remote,
                f"refs/heads/{main_branch}",
                f"refs/heads/{development_branch}",
                f"refs/tags/{tag_name}",
                f"refs/tags/{tag_name}^{{}}",
            ],
            root=root,
        )
        _require(
            result.returncode == 0,
            f"remote release read: {remote}",
            "git ls-remote exit code 0",
            f"exit code {result.returncode}",
            "restore read-only remote connectivity and rerun with --remote",
        )
        refs = {}
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) == 2:
                refs[fields[1]] = fields[0]
        _require(
            refs.get(f"refs/heads/{main_branch}") == head,
            f"remote main branch target: {remote}",
            head,
            refs.get(f"refs/heads/{main_branch}", "missing"),
            "do not push automatically; inspect and complete the authorized main publication",
        )
        _require(
            refs.get(f"refs/heads/{development_branch}") == head,
            f"remote development branch target: {remote}",
            head,
            refs.get(f"refs/heads/{development_branch}", "missing"),
            "do not push automatically; inspect and complete the authorized development publication",
        )
        if state["state"] == "RELEASED":
            _require(
                refs.get(f"refs/tags/{tag_name}^{{}}") == state["release_commit"],
                f"remote released tag target: {remote}",
                state["release_commit"],
                refs.get(f"refs/tags/{tag_name}^{{}}", "missing"),
                "do not push or overwrite automatically; inspect remote release state",
            )
        else:
            tag_refs = tuple(ref for ref in refs if ref.startswith(f"refs/tags/{tag_name}"))
            _require(
                not tag_refs,
                f"remote pre-release tag state: {remote}",
                f"no {tag_name} tag",
                tag_refs,
                "stop and inspect the unexpected remote tag",
            )


def release_check(
    version: str,
    *,
    remote: bool,
    root: Path = REPOSITORY_ROOT,
) -> int:
    state = _load_release_state(root)
    _require(
        version == state["version"],
        "requested release version",
        state["version"],
        version,
        "use the version declared by the reviewed release metadata",
    )
    branch = _git_output(["branch", "--show-current"], root=root)
    head = _git_output(["rev-parse", "HEAD"], root=root)
    if state["schema_version"] == "v1":
        expected_branch = state["expected_branch"]
    elif state["state"] == "RELEASED":
        expected_branch = state["expected_main_branch"]
    else:
        expected_branch = state["expected_development_branch"]
    _require(
        branch == expected_branch,
        "release branch",
        expected_branch,
        branch or "detached HEAD",
        "switch to the reviewed release branch without rewriting history",
    )
    _release_worktree_check(root)
    code_version = _read_code_version(root)
    _require(
        code_version == version,
        "project version consistency",
        version,
        code_version,
        "update only the project version in the reviewed implementation commit",
    )
    required_documents = state["required_documents"]
    if state["schema_version"] == "v2":
        final_qa_path = root / state["final_qa_evidence"]
        _require(
            final_qa_path.is_file(),
            "Final QA evidence",
            f"reviewed evidence at {state['final_qa_evidence']}",
            "missing",
            "run independent Final Release QA and commit its real evidence before release",
        )
    for relative_path in required_documents:
        path = root / relative_path
        _require(
            path.is_file(),
            f"release document: {relative_path}",
            "existing tracked file",
            "missing",
            f"create and review the required V{version} release document",
        )
        if state["schema_version"] == "v1":
            content = path.read_text(encoding="utf-8")
            sentinel = state["document_sentinel"]
            _require(
                sentinel in content,
                f"release document sentinel: {relative_path}",
                sentinel,
                "missing",
                "add the stable reviewed release-state sentinel without rewriting frozen history",
            )
    readme = (root / "README.md").read_text(encoding="utf-8")
    _require(
        f"### V{version}" in readme,
        "README Version History",
        f"a V{version} version-history heading",
        "missing",
        f"add the concise V{version} maintenance release entry",
    )
    baseline = state["baseline"]
    _require(
        baseline
        == {"version": BASELINE_VERSION, "commit": BASELINE_RELEASE_COMMIT, "tag": BASELINE_TAG},
        "released baseline metadata",
        {"version": BASELINE_VERSION, "commit": BASELINE_RELEASE_COMMIT, "tag": BASELINE_TAG},
        baseline,
        "restore the immutable V3.1.0 release baseline reference",
    )
    baseline_target = _git_output(["rev-parse", f"{BASELINE_TAG}^{{}}"], root=root)
    _require(
        baseline_target == BASELINE_RELEASE_COMMIT,
        f"V{BASELINE_VERSION} baseline tag target",
        BASELINE_RELEASE_COMMIT,
        baseline_target,
        "do not overwrite the released tag; investigate repository history",
    )
    _verify_tag_state(version, state, root)
    validate_archive_v310(root=root)
    if remote:
        if state["schema_version"] == "v1":
            _remote_tag_check(version, state, root)
        else:
            _remote_release_check(version, state, root, head)
    print("release_check=PASS")
    print(f"version={version}")
    print(f"state={state['state']}")
    print(f"branch={branch}")
    print(f"head={head}")
    print(f"remote_check={'enabled' if remote else 'disabled'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("doctor", help="diagnose the core, test, Git, and optional E5 environments")
    commands.add_parser("project-smoke", help="run a tiny offline Project Intelligence smoke check")

    test = commands.add_parser("test", help="run a stable repository test profile")
    test.add_argument("profile", choices=tuple(TEST_PROFILES))
    test.add_argument("pytest_args", nargs=argparse.REMAINDER)

    model = commands.add_parser("model-check", help="validate an existing frozen E5 snapshot offline")
    location = model.add_mutually_exclusive_group()
    location.add_argument("--cache-dir", type=Path)
    location.add_argument("--model-path", type=Path)
    model.add_argument("--smoke", action="store_true")

    experiment = commands.add_parser(
        "experiment-validate",
        help="validate the frozen V3.1.0 archive or committed execution prerequisites",
    )
    experiment.add_argument("target", nargs="?", choices=("archive-v3.1.0",))
    experiment.add_argument("--purpose", choices=("dry-run", "formal"))

    release = commands.add_parser("release-check", help="run a read-only release consistency gate")
    release.add_argument("--version", required=True)
    release.add_argument("--remote", action="store_true")
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(arguments)
    try:
        if args.command == "doctor":
            return doctor()
        if args.command == "project-smoke":
            return project_smoke()
        if args.command == "test":
            return run_test_profile(args.profile, args.pytest_args)
        if args.command == "model-check":
            return model_check(cache_dir=args.cache_dir, model_path=args.model_path, smoke=args.smoke)
        if args.command == "experiment-validate":
            if args.target is None and args.purpose is None:
                parser.error("experiment-validate requires archive-v3.1.0 or --purpose")
            if args.target == "archive-v3.1.0":
                validate_archive_v310()
            if args.purpose is not None:
                experiment_preflight(args.purpose)
            return 0
        if args.command == "release-check":
            return release_check(args.version, remote=args.remote)
    except WorkflowError as error:
        _print_failure(error)
        return 1
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
