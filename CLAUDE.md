# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Refactron is a Python library and CLI tool for code analysis, refactoring, and technical debt elimination. It uses AST-based analysis (libcst, astroid), AI-powered suggestions (Groq/Llama 3), and a RAG system (ChromaDB) for context-aware code intelligence. Version 1.0.15 → 1.1.0 (MVP in progress), Python 3.8+, MIT license.

**Active development branch:** `main` (MVP v1.1.0 — adding Verification Engine, `--dry-run`, `--verify`). See `dev-notes/Refactron_Comprehensive_MVP.md` for the full roadmap.

## Build & Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run all tests (with coverage by default via pyproject.toml addopts)
pytest

# Run a single test file
pytest tests/test_analyzers.py

# Run a single test
pytest tests/test_analyzers.py::TestClassName::test_method_name

# Run tests without coverage
pytest --no-cov

# Formatting
black refactron tests --line-length=100
isort refactron tests --profile=black

# Linting
flake8 refactron --max-line-length=100

# Type checking (strict for src, relaxed for tests/examples/benchmarks)
mypy refactron

# Run all pre-commit hooks
pre-commit run --all-files

# CLI entry point
refactron
```

## Code Style

- **Line length**: 100 (enforced by black, isort, flake8)
- **Formatter**: black with `target-version = ["py38", "py39", "py310", "py311"]`
- **Import sorting**: isort with `profile = "black"`
- **Type annotations**: Required in `refactron/` (mypy `disallow_untyped_defs = true`), not required in tests/examples/benchmarks

## Architecture

### Entry Points
- **CLI**: `refactron/cli/` package → `refactron/cli/main.py:main` (Click group). Entry point: `refactron.cli:main`. Subcommands split across `analysis.py`, `refactor.py`, `patterns.py`, `rag.py`, `cicd.py`, `repo.py`, `auth.py`
- **Python API**: `Refactron` class from `refactron/core/refactron.py`, exported via `__init__.py` using lazy imports (heavy modules only load when accessed)

### Core Modules
- **`core/`** — Central orchestration: `Refactron` main class, `RefactronConfig` (YAML-backed with versioning), models, backup/rollback, AST cache, incremental analysis, parallel processing, false positive tracking, workspace management, credentials/device auth, logging config, Prometheus metrics, telemetry, OpenTelemetry
- **`analyzers/`** — Plugin-based code analyzers (7: complexity, code smell, security, performance, dead code, dependency, type hint). All extend `BaseAnalyzer`
- **`refactorers/`** — Plugin-based refactorers (5: extract method, add docstring, magic number, reduce parameters, simplify conditionals). All extend `BaseRefactorer`
- **`analysis/`** — Semantic analysis layer: CFG builder (`cfg/`), data flow analysis, taint analysis (source-to-sink tracking), symbol table (maps classes/functions/variables across codebase), type inference engine (`core/inference.py`)
- **`autofix/`** — Automated fix engine with fixers, risk scoring, and safety previews
- **`patterns/`** — Pattern learning system: fingerprinting, learning, matching, ranking, storage, tuning
- **`llm/`** — LLM integration: orchestrator, Groq client, backend client, prompts, safety checks
- **`rag/`** — RAG system: code indexing, chunking, parsing, retrieval (ChromaDB + sentence-transformers)
- **`cicd/`** — CI/CD integrations: GitHub Actions, GitLab CI, pre-commit hooks, PR integration, quality gates

### Key Design Patterns
- **Plugin architecture**: Analyzers and refactorers register via base classes and are discovered by the core `Refactron` class
- **Safety-first refactoring**: All refactoring goes through preview → backup → apply → optional rollback
- **AST-based**: Uses libcst for concrete syntax tree manipulation (preserves formatting) and astroid for advanced analysis
- **Auth-gated CLI**: All CLI commands except `login`/`logout`/`auth` check for a valid access token (stored via `core/credentials.py`) before proceeding

### MVP v1.1.0 Work in Progress

| Day | Feature | Status |
|-----|---------|--------|
| 1 | Exception isolation for TaintAnalyzer/DataFlowAnalyzer (`AnalysisSkipWarning`, skip-rate tracking) | ✅ Done |
| 2 | SHA-256 hardening for `IncrementalAnalysisTracker`; backup integrity validation in `BackupManager` | ✅ Done |
| 3 | `--dry-run` flag for `refactron autofix`; `generate_diff()` in `autofix/file_ops.py`; `AutoFixEngine.fix_file()` | ✅ Done |
| 4 | Test fixture files in `tests/fixtures/` (6 files, 8 fixture validation tests) | ✅ Done |
| 5 | Phase 1 gate: 758 tests green, self-analysis 96 files/0 crashes, added `--no-cache` flag to `analyze` | ✅ Done |
| 6-7 | VerificationResult/CheckResult data contracts, BaseCheck ABC, VerificationEngine skeleton | ✅ Done |
| 8 | SyntaxVerifier (Check 1): ast.parse, CST roundtrip, dangerous calls, import count | ✅ Done |
| 9 | ImportIntegrityVerifier (Check 2): removed imports, dotted access, new import resolution | ✅ Done |
| 10 | TestSuiteGate (Check 3): reverse import graph, swap-and-restore, subprocess pytest | ✅ Done |
| 11-12 | Wire into AutoFixEngine.fix_file(verify=True), --verify CLI flag, report.py | ✅ Done |
| 13-15 | Full fixture validation, Phase 2 gate check (827 tests green) | ✅ Done |

**Key new APIs (Day 1–3):**
- `AnalysisSkipWarning` dataclass in `core/models.py` — surfaced on `AnalysisResult.semantic_skip_warnings`
- `BackupManager.validate_backup_integrity(session_id)` → `(valid_paths, corrupt_paths)`
- `generate_diff(original, modified, filename)` in `autofix/file_ops.py` — returns unified diff string
- `AutoFixEngine.fix_file(file_path, issues, dry_run=True, verify=False)` → `(fixed_code, diff_or_None)`

**Key new APIs (Phase 2 — Verification Engine):**
- `VerificationEngine(project_root).verify(original, transformed, file_path)` → `VerificationResult`
- `CheckResult` / `VerificationResult` — frozen dataclasses in `verification/result.py`
- `BaseCheck` ABC in `verification/engine.py` — 3 implementations: `SyntaxVerifier`, `ImportIntegrityVerifier`, `TestSuiteGate`
- `format_verification_result(result, console)` — Rich CLI output in `verification/report.py`
- `--verify` flag on `refactron autofix` — runs verification pipeline before applying fixes

**CLI output overhaul:**
- `refactron analyze` now shows an **interactive issue viewer** (TTY) with severity-grouped navigation (`[1-4]` to drill in, `[n/p/b/q]` to navigate)
- Non-interactive fallback for CI/CD (piped output or `--no-interactive` flag)
- Issues grouped by severity (CRITICAL → ERROR → WARNING → INFO)
- Relative file paths instead of absolute
- Code context (3 lines) for critical/warning/error issues
- Logger noise suppressed (use `--log-level INFO` to re-enable)
