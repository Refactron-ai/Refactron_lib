+-----------------------------------------------------------------------+
| **REFACTRON**                                                         |
|                                                                       |
| Comprehensive MVP Plan                                                |
|                                                                       |
| *Safety-First Refactoring for Production Codebases*                   |
|                                                                       |
|                                                                       |
|  ---------------------- ---------------------- ---------------------- |
|   **v1.1.0**             **5 Weeks**            **March 2026**        |
|                                                                       |
|                                                                       |
|  ---------------------- ---------------------- ---------------------- |
|                                                                       |
| Repo Connect: ✅ COMPLETE \| Current: v1.0.15 on PyPI                 |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
| **🎯 North Star --- The One Sentence That Governs Every Decision**    |
|                                                                       |
| \"I ran Refactron on my production codebase. It found real issues,    |
| fixed the safe ones,                                                  |
|                                                                       |
| and proved --- with evidence --- that nothing would break.\"          |
|                                                                       |
| Every feature in this plan exists to make a developer able to say     |
| that sentence.                                                        |
|                                                                       |
| If a feature does not serve that sentence, it is not in this MVP.     |
+-----------------------------------------------------------------------+

**Contents**

**Part 1 --- What We Are Starting From**

**1.1 What Is Confirmed Built and Stable**

The following modules are live at v1.0.15 on PyPI. They are tested,
functional, and ship as-is in the MVP. The mandate is to stabilise them
--- not rewrite them.

  -------------------------- ------------------------ --------------------------
  **Module**                 **Location**             **Status**

  **Core Orchestrator**      *core/refactron.py*      **✅ Stable --- ship
                                                      as-is**

  **8 Rule Analyzers**       *analyzers/*             **✅ Stable --- 96.8% test
                                                      coverage**

  **5 Complex Refactorers**  *refactorers/*           **✅ Stable**

  **14 Auto-Fixers**         *autofix/*               **✅ Stable --- needs
                                                      \--dry-run flag added**

  **BackupRollbackSystem**   *core/backup.py*         **✅ Stable --- reactive
                                                      only, pre-MVP**

  **AST Cache +              *core/cache.py*          **✅ Stable --- needs
  Incremental**                                       SHA-256 hash fix**

  **CI/CD Gateway**          *cicd/*                  **✅ Stable**

  **CLI (10 commands)**      *cli.py*                 **✅ Stable**

  **Config System (YAML)**   *core/config\*.py*       **✅ Stable**

  **Repo Connect**           *cli/repo.py*            **✅ COMPLETE --- excluded
                                                      from MVP scope**
  -------------------------- ------------------------ --------------------------

**1.2 What Is Partial and Needs Gating**

These modules exist but are not reliable enough to ship as default
behavior. They will be wrapped in exception isolation and kept in
dispatch with visible warnings (Option B decision). They are NOT
disabled --- they fail transparently.

  ---------------------- ------------------------- --------------------------
  **Module**             **Location**              **Required Action**

  **LLM Orchestrator**   *llm/*                    **🟡 No reliability layer
                                                   --- exclude from MVP
                                                   entirely**

  **RAG System**         *rag/*                    **🟡 No quality validation
                                                   --- exclude from MVP
                                                   entirely**

  **TaintAnalyzer**      *analysis/taint.py*       **🟡 Wrap in try/except
                                                   --- show visible skip
                                                   warning**

  **DataFlowAnalyzer**   *analysis/data_flow.py*   **🟡 Wrap in try/except
                                                   --- show visible skip
                                                   warning**

  **SafetyGate**         *llm/safety.py*           **🟡 Guards LLM only ---
                                                   not relevant without LLM
                                                   in MVP**
  ---------------------- ------------------------- --------------------------

+-----------------------------------------------------------------------+
| **⚠️ Option B Decision --- Transparent Degradation, Not Silent        |
| Failure**                                                             |
|                                                                       |
| TaintAnalyzer and DataFlowAnalyzer stay in the dispatch pipeline,     |
| exception-isolated.                                                   |
|                                                                       |
| When they hit an unusual AST node, output must show:                  |
|                                                                       |
| ⚠ TaintAnalyzer skipped src/api/views.py --- Unsupported AST node     |
| (walrus operator, line 47)                                            |
|                                                                       |
| ⚠ This file was NOT checked for taint vulnerabilities.                |
|                                                                       |
| A file that was skipped must NEVER appear the same as a file that was |
| checked and found clean.                                              |
|                                                                       |
| Track and display the skip rate. If it exceeds 10% of files, escalate |
| to hardening immediately.                                             |
+-----------------------------------------------------------------------+

**1.3 The Critical Gap --- What Is Completely Missing**

+-----------------------------------------------------------------------+
| **🔴 The Gap Between the Motto and the Reality**                      |
|                                                                       |
| Motto: \"Safety-First Refactoring for Production Codebases\"          |
|                                                                       |
| Current reality: BackupRollback (recovers after failure).             |
| FixRiskLevel (a label, not a proof).                                  |
|                                                                       |
| Neither of these PROVES a transform is safe before the filesystem is  |
| modified.                                                             |
|                                                                       |
| The Verification Engine --- the system that actually proves safety    |
| --- does not exist yet.                                               |
|                                                                       |
| Building it is the entire MVP.                                        |
+-----------------------------------------------------------------------+

  ---------------------- ------------------------------------------------
  **Missing System**     **Why This Is Critical**

  **Verification         Nothing currently proves a transform is safe
  Engine**               before the real file is touched

  **\--dry-run on        Developers cannot preview changes without
  autofix**              writing to disk --- table-stakes for any autofix
                         tool

  **Test Suite Gate**    Existing tests are never run after a transform
                         --- regression breakage goes undetected

  **refactron verify     The standalone CLI command that proves safety
  command**              does not exist

  **Import Integrity     No detection of broken imports or new circular
  Check**                dependencies after a transform

  **SHA-256 cache        mtime-only cache will serve stale ASTs after
  invalidation**         file edits --- wrong analysis results
  ---------------------- ------------------------------------------------

**Part 2 --- Definitive MVP Scope**

+-----------------------------------------------------------------------+
| **📌 The Single Decision Filter**                                     |
|                                                                       |
| \"Does this feature directly prove that a refactoring is safe?\"      |
|                                                                       |
| If yes → it is in the MVP.                                            |
|                                                                       |
| If no → write it in BACKLOG.md and do not touch it until after the    |
| MVP ships.                                                            |
|                                                                       |
| This filter has already been applied. Everything below passed it.     |
+-----------------------------------------------------------------------+

**2.1 The Five Hero Commands --- Nothing More**

These five commands are the entire MVP. They must work flawlessly on any
real Python codebase before v1.1.0 ships. Not four of five. All five.

  ---------------------------- ------------------------------------------
  **Command**                  **What It Proves**

  **refactron analyze .**      Deep static analysis --- 8 analyzers, rich
                               output grouped by severity, actionable
                               messages

  **refactron autofix .        Preview every proposed fix as a unified
  \--dry-run**                 diff --- nothing written to disk

  **refactron autofix .        Apply only fixes that pass all 3
  \--verify**                  verification checks --- block everything
                               else

  **refactron verify \<file\>  Standalone verification --- runs all 3
  \--against \<original\>**    checks, usable in CI without autofix

  **refactron rollback**       Undo any applied fix --- restores from
                               backup, zero developer action required
  ---------------------------- ------------------------------------------

**2.2 What Is Explicitly NOT In This MVP**

These belong in BACKLOG.md. Writing them here so they are acknowledged
and then closed.

  ------------------------ ----------------------------------------------
  **Feature**              **Why Post-MVP**

  LLM / RAG Integration    Verification must work perfectly without AI.
                           Intelligence is layered on top of proven
                           safety.

  Pattern Learning Engine  Requires real user feedback data to produce
                           anything meaningful. Useless before users
                           exist.

  Semantic Equivalence     Post-MVP verification layer. Added after test
  Check                    gate is proven solid.

  Type Consistency Check   Optional, configurable. Not needed to prove
  (mypy)                   basic safety.

  SARIF Output Format      Enterprise CI unlock. Prioritise after SMB
                           validation.

  Prometheus / Telemetry   No users means nothing meaningful to observe.

  refactron init command   Quality of life. Does not prove safety.

  VSCode Extension         CLI must be perfect first. Extension is CLI
                           under the hood.

  Multi-Language Support   Python-only until the model is validated.
  ------------------------ ----------------------------------------------

**2.3 Version: v1.1.0, Not v2.0.0**

The Verification Engine is additive functionality. It is a new
subcommand and a new flag on autofix. No existing command behavior
changes. No existing config format changes. No breaking API changes.
**Per SemVer, this is v1.1.0.**

A v2.0.0 bump would scare existing users and break anyone with
refactron\>=1.0,\<2 in their requirements. Reserve v2.0.0 for when the
core CLI interface needs fundamental restructuring.

**Part 3 --- Verification Engine Architecture**

**This is the most important engineering work in the entire MVP.
Everything else is polish. The Verification Engine is the reason v1.1.0
is a different product from v1.0.15.**

**3.1 The Inviolable Safety Rule**

+-----------------------------------------------------------------------+
| **The Original File Is Never Modified During Verification**           |
|                                                                       |
| All verification checks run against a temp file in an isolated        |
| subprocess.                                                           |
|                                                                       |
| The real file is written to disk ONLY after safe_to_apply is True.    |
|                                                                       |
| *This single rule --- not a sandbox, not a container --- is the       |
| safety guarantee.*                                                    |
+-----------------------------------------------------------------------+

**3.2 Module Structure**

+-----------------------------------------------------------------------+
| **refactron/verification/**                                           |
|                                                                       |
| ├── \_\_init\_\_.py                                                   |
|                                                                       |
| ├── engine.py ← VerificationEngine (main orchestrator --- called by   |
| AutoFixEngine)                                                        |
|                                                                       |
| ├── result.py ← VerificationResult (locked data contract --- define   |
| before any code)                                                      |
|                                                                       |
| ├── report.py ← VerificationReport (human-readable CLI output)        |
|                                                                       |
| └── checks/                                                           |
|                                                                       |
| ├── syntax.py ← SyntaxVerifier (Check 1 --- always runs, \< 50ms)     |
|                                                                       |
| ├── imports.py ← ImportIntegrityVerifier (Check 2 --- always runs, \< |
| 100ms)                                                                |
|                                                                       |
| └── test_gate.py ← TestSuiteGate (Check 3 --- runs when tests exist,  |
| 2--30s)                                                               |
+-----------------------------------------------------------------------+

**3.3 The VerificationResult Contract**

Lock this dataclass before writing a single line of verification logic.
**Every downstream module --- AutoFixEngine, CLI output, tests ---
depends on this schema. Do not change it once locked.**

  ---------------------- ------------------- ------------------------------------
  **Field**              **Type**            **Purpose**

  **safe_to_apply**      *bool*              THE only field AutoFixEngine reads.
                                             False = nothing is written. No
                                             exceptions in code.

  **passed**             *bool*              All checks completed without a
                                             blocking failure

  **checks_run**         *List\[str\]*       Names of every check that executed
                                             in this run

  **checks_passed**      *List\[str\]*       Names of checks that returned a
                                             clean result

  **checks_failed**      *List\[str\]*       Names of checks that blocked the
                                             transform

  **blocking_reason**    *Optional\[str\]*   Shown to developer when blocked ---
                                             must be actionable, not a stack
                                             trace

  **confidence_score**   *float 0.0--1.0*    Composite confidence across all
                                             checks that passed

  **verification_ms**    *int*               Total wall-clock time for the full
                                             verification run in milliseconds

  **skipped_checks**     *List\[str\]*       Checks that were skipped (e.g. no
                                             tests found) --- distinct from
                                             passed or failed
  ---------------------- ------------------- ------------------------------------

**3.4 The Three MVP Verification Checks**

  ------- ----------------- --------------- ----------------------------------
          **Check Name**    **Speed**       **What It Catches**

  **1**   **Syntax          \< 50ms Always  Parse errors, CST corruption from
          Validation**      runs            transform bugs, newly introduced
                                            eval()/exec() calls, import count
                                            drop

  **2**   **Import          \< 100ms Always Removed imports still used in
          Integrity**       runs            code, new imports that cannot
                                            resolve, circular dependencies
                                            introduced

  **3**   **Test Suite      2--30s Runs if  Any test breakage in files that
          Gate**            tests exist     import the changed module.
                                            Import-graph mapped --- NOT full
                                            suite. Hard kill at 45s.
  ------- ----------------- --------------- ----------------------------------

**3.5 How Check 3 Maps Tests to Changed Files**

Running the full test suite after every autofix is not practical. The
Test Suite Gate uses an import-graph mapper to find only the tests that
actually import the changed module.

-   Build a reverse import graph at analysis time: for every .py file,
    record which modules it imports.

-   When a file is transformed, look up that file in the reverse graph
    to find all files that import it.

-   Filter those files to only test files (names starting with test\_ or
    in a tests/ directory).

-   Run only those test files via subprocess: pytest \--timeout=30 -x -q
    \<relevant_test_files\>

-   If no test files import the changed module --- pass with note \"No
    tests cover this module.\"

-   If pytest exits non-zero for any reason --- block. Show the first
    failing test output.

-   Hard kill at 45 seconds regardless of outcome --- never block a
    developer workflow.

**3.6 The Atomic Write Protocol**

This is the technical implementation of the safety rule from Section
3.1. The sequence is non-negotiable.

  ------- -------------------------------------------------------------------
  **1**   Generate the transformed code in memory. The real file has not been
          touched.

  **2**   Write transformed code to a temp file in the SAME directory as the
          target (same filesystem required for atomic move).

  **3**   Run all 3 verification checks against the temp file path, not the
          real path.

  **4**   If ANY check sets safe_to_apply = False: delete the temp file, show
          blocking_reason, restore from backup if needed. Done.

  **5**   If safe_to_apply = True: call os.replace(tmp_path, real_path). This
          is atomic on POSIX --- no partial write is possible.

  **6**   Preserve original file permissions on the replaced file.

  **7**   Delete the temp file in a finally block --- it must never be left
          on disk regardless of outcome.
  ------- -------------------------------------------------------------------

**Part 4 --- The 5-Week Execution Plan**

+-----------------------------------------------------------------------+
| **⚠️ Why 5 Weeks Is The Right Number**                                |
|                                                                       |
| The previous 16-week plan was a v2.0 product roadmap. An MVP ships in |
| 5 weeks.                                                              |
|                                                                       |
| Repo connect is already done --- this removes \~4 days from the       |
| original critical path.                                               |
|                                                                       |
| 5 weeks gives buffer for the hardest part (Test Suite Gate) without   |
| over-engineering everything else.                                     |
|                                                                       |
| Week 5 is validation, not building. You ship what Week 4 produces,    |
| not what Week 5 imagines.                                             |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
| **PHASE 1** Stabilize What Exists Week 1 · Days 1--5                  |
+-----------------------------------------------------------------------+
| **Goal: Zero crashes running refactron analyze refactron/ on the      |
| library itself**                                                      |
|                                                                       |
| This is the stability baseline. No new features. No Verification      |
| Engine code. Just making what exists rock-solid.                      |
|                                                                       |
| **Day 1 --- Exception Isolation for All Analyzers**                   |
|                                                                       |
| -   Wrap every analyzer in try/except in the dispatcher --- one bad   |
|     AST node must NEVER crash the full run                            |
|                                                                       |
| -   TaintAnalyzer and DataFlowAnalyzer: on exception, emit a visible  |
|     ⚠ warning showing the file and reason                             |
|                                                                       |
| -   Warning format: *⚠ TaintAnalyzer skipped src/api.py ---           |
|     Unsupported node (line 47). This file was NOT checked for taint.* |
|                                                                       |
| -   Add skip_rate counter --- track files analyzed vs skipped per     |
|     analyzer run                                                      |
|                                                                       |
| -   If skip_rate \> 10% at run end, add a summary warning in the CLI  |
|     output                                                            |
|                                                                       |
| **Day 2 --- Cache Hardening + Backup Validation**                     |
|                                                                       |
| -   Replace mtime-only AST cache invalidation with SHA-256 file hash  |
|     --- mtime alone is unreliable                                     |
|                                                                       |
| -   Add \--no-cache flag for debugging and reproducibility in CI      |
|     environments                                                      |
|                                                                       |
| -   Test BackupRollbackSystem when git is NOT initialized --- verify  |
|     plain file backup path works correctly                            |
|                                                                       |
| -   Add file integrity hash check before and after every transform    |
|     --- detect silent corruption                                      |
|                                                                       |
| **Day 3 --- Dry-Run Mode (Table-Stakes for Any Autofix Tool)**        |
|                                                                       |
| -   Add \--dry-run flag to **refactron autofix** --- shows unified    |
|     diff, writes nothing to disk                                      |
|                                                                       |
| -   Dry-run output format: coloured unified diff per file, summary of |
|     what would change                                                 |
|                                                                       |
| -   Add \--diff flag as alias for \--dry-run for discoverability      |
|                                                                       |
| -   This is the single most important UX addition --- no developer    |
|     trusts autofix without preview                                    |
|                                                                       |
| **Day 4 --- Test Harness Construction**                               |
|                                                                       |
| -   Create tests/fixtures/ directory with 5 Python files containing   |
|     known issues:                                                     |
|                                                                       |
|     -   fixture_sql_injection.py --- raw SQL with f-string user input |
|                                                                       |
|     -   fixture_unused_imports.py --- 6 unused imports across 3 files |
|                                                                       |
|     -   fixture_complexity.py --- function with cyclomatic complexity |
|         18                                                            |
|                                                                       |
|     -   fixture_bad_extract.py --- function extraction that changes   |
|         return type (known-bad transform)                             |
|                                                                       |
|     -   fixture_safe_extract.py --- function extraction that is       |
|         provably safe (known-good transform)                          |
|                                                                       |
| -   Write integration test: full analyze → autofix → rollback cycle   |
|     on fixture project passes                                         |
|                                                                       |
| **Day 5 --- Gate Check**                                              |
|                                                                       |
| -   Run: **refactron analyze refactron/** --- the library analyzing   |
|     itself                                                            |
|                                                                       |
| -   Fix every crash, every confusing error message, every missing     |
|     exception handler found                                           |
|                                                                       |
| -   All 135+ existing tests must still pass --- no regressions from   |
|     Days 1--4                                                         |
|                                                                       |
| -   Record baseline: how many files analyzed, how many skipped, what  |
|     the output looks like                                             |
|                                                                       |
| +------------------------------------------------------------------+  |
| | **✅ Week 1 Gate --- Must Pass Before Week 2 Starts**            |  |
| |                                                                  |  |
| | refactron analyze refactron/ completes with zero crashes.        |  |
| |                                                                  |  |
| | All 135+ existing tests pass.                                    |  |
| |                                                                  |  |
| | TaintAnalyzer skip warnings are visible and correctly formatted. |  |
| |                                                                  |  |
| | \--dry-run shows a diff without writing any files.               |  |
| +------------------------------------------------------------------+  |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
| **PHASE 2** Build the Verification Engine Weeks 2--3 · Days 6--15     |
+-----------------------------------------------------------------------+
| **Goal: Verification Engine blocks 100% of known-bad transforms in    |
| the fixture test suite**                                              |
|                                                                       |
| This is the hardest engineering work in the MVP. Ten days. Three      |
| checks. One data contract. Nothing else.                              |
|                                                                       |
| **Days 6--7 --- Lock the Contract, Write the Failing Test**           |
|                                                                       |
| -   Create refactron/verification/ directory structure as specified   |
|     in Section 3.2                                                    |
|                                                                       |
| -   Define **VerificationResult** in result.py --- lock every field   |
|     as specified in Section 3.3                                       |
|                                                                       |
| -   Write tests/verification/test_blocks_bad_transform.py --- this    |
|     test MUST fail on Day 6                                           |
|                                                                       |
| -   The fixture: fixture_bad_extract.py contains a function           |
|     extraction that changes the return type                           |
|                                                                       |
| -   The test asserts that VerificationEngine.verify() returns         |
|     safe_to_apply=False on this fixture                               |
|                                                                       |
| -   **The entire Days 8--15 effort is making this single test pass.** |
|                                                                       |
| **Days 8--9 --- Check 1: Syntax Validation**                          |
|                                                                       |
| -   SyntaxVerifier.verify(original_code, transformed_code) →          |
|     VerificationResult                                                |
|                                                                       |
| -   Step 1: Attempt libcst.parse_module(transformed_code) ---         |
|     ParserSyntaxError = block immediately                             |
|                                                                       |
| -   Step 2: CST round-trip --- parse → unparse → re-parse. If second  |
|     parse fails, CST was corrupted by transform                       |
|                                                                       |
| -   Step 3: AST walk on transformed code --- block if any new         |
|     ast.Call to eval/exec/os.system found                             |
|                                                                       |
| -   Step 4: Compare import counts --- if transformed has fewer import |
|     statements, check if removed imports are still referenced         |
|                                                                       |
| -   Target: \< 50ms on a 500-line file. If slower, profile and        |
|     optimise before moving to Check 2.                                |
|                                                                       |
| **Days 10--11 --- Check 2: Import Integrity**                         |
|                                                                       |
| -   ImportIntegrityVerifier.verify(original_path, transformed_code) → |
|     VerificationResult                                                |
|                                                                       |
| -   Step 1: Extract all import statements from original and           |
|     transformed using ast.walk()                                      |
|                                                                       |
| -   Step 2: For every import that existed in original but is absent   |
|     in transformed --- check if that name is still referenced in the  |
|     code. If yes, block.                                              |
|                                                                       |
| -   Step 3: For every new import in transformed that was not in       |
|     original --- attempt importlib.util.find_spec(module_name). If    |
|     returns None, block.                                              |
|                                                                       |
| -   Step 4: Build directed import graph, run DFS cycle detection. If  |
|     new cycle introduced, block.                                      |
|                                                                       |
| -   Edge cases to handle: TYPE_CHECKING blocks, relative imports,     |
|     conditional imports inside if statements --- warn on these, do    |
|     not block                                                         |
|                                                                       |
| **Days 12--14 --- Check 3: Test Suite Gate**                          |
|                                                                       |
| -   TestSuiteGate.verify(changed_file, transformed_code) →            |
|     VerificationResult                                                |
|                                                                       |
| -   Step 1: Write transformed_code to a NamedTemporaryFile in the     |
|     same directory as changed_file (delete=False)                     |
|                                                                       |
| -   Step 2: Build reverse import graph from project root --- find all |
|     test files that transitively import changed_file                  |
|                                                                       |
| -   Step 3: If no test files found → return VerificationResult with   |
|     checks_passed=\[\"test_gate\"\], note=\"No tests cover this       |
|     module\"                                                          |
|                                                                       |
| -   Step 4: Run subprocess.run(\[\"pytest\", \"\--timeout=30\",       |
|     \"-x\", \"-q\", \*relevant_test_files\], timeout=45,              |
|     capture_output=True)                                              |
|                                                                       |
| -   Step 5: returncode == 0 → pass. Any other returncode → block with |
|     first 500 chars of stdout as blocking_reason                      |
|                                                                       |
| -   Step 6: Always unlink temp file in finally block --- no orphaned  |
|     files on disk ever                                                |
|                                                                       |
| -   Step 7: Hard kill: if subprocess times out at 45s → block with    |
|     \"Test suite gate timed out (45s limit)\"                         |
|                                                                       |
| **Day 15 --- Wire into AutoFixEngine + Integration Tests**            |
|                                                                       |
| -   AutoFixEngine calls VerificationEngine.verify(original_code,      |
|     transformed_code, file_path) before every os.write call           |
|                                                                       |
| -   If result.safe_to_apply is False: log result.blocking_reason,     |
|     restore from backup, show in CLI output                           |
|                                                                       |
| -   If result.safe_to_apply is True: execute atomic write protocol    |
|     from Section 3.6                                                  |
|                                                                       |
| -   Run full fixture test suite: fixture_bad_extract must be blocked, |
|     fixture_safe_extract must be allowed                              |
|                                                                       |
| -   Verify that the inviolable safety rule holds: original file is    |
|     never modified when any check fails                               |
|                                                                       |
| +------------------------------------------------------------------+  |
| | **✅ Week 3 Gate --- Must Pass Before Week 4 Starts**            |  |
| |                                                                  |  |
| | VerificationEngine correctly blocks fixture_bad_extract.py       |  |
| | (type-changing extraction).                                      |  |
| |                                                                  |  |
| | VerificationEngine correctly allows fixture_safe_extract.py      |  |
| | (unused import removal).                                         |  |
| |                                                                  |  |
| | 100% accuracy on the complete fixture test suite --- no          |  |
| | exceptions.                                                      |  |
| |                                                                  |  |
| | Original file integrity verified: never modified when            |  |
| | safe_to_apply is False.                                          |  |
| |                                                                  |  |
| | test_blocks_bad_transform.py is now GREEN.                       |  |
| +------------------------------------------------------------------+  |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
| **PHASE 3** Hero Commands + Output Quality + Real-World Testing Week  |
| 4 · Days 16--20                                                       |
+-----------------------------------------------------------------------+
| **Goal: pip install refactron && refactron analyze . produces useful, |
| verified output in under 2 minutes**                                  |
|                                                                       |
| Engineering is done. This week is about whether a developer who has   |
| never seen Refactron can use it without help.                         |
|                                                                       |
| **Day 16 --- Output Quality Overhaul**                                |
|                                                                       |
| -   Group issues by file, then by severity: CRITICAL → HIGH → MEDIUM  |
|     → LOW                                                             |
|                                                                       |
| -   Show the problematic line of code inline beneath each issue ---   |
|     not just a line number                                            |
|                                                                       |
| -   Add summary line at the bottom: \"3 critical · 7 high · 14 medium |
|     (run \--autofix \--verify to fix 16)\"                            |
|                                                                       |
| -   Add \--format json for CI parsing and script consumption          |
|                                                                       |
| -   Add \--fail-on CRITICAL flag for CI quality gate exit codes       |
|     (exits 1 if any CRITICAL found)                                   |
|                                                                       |
| -   Error messages: replace every stack trace with a human-readable   |
|     message + suggested action                                        |
|                                                                       |
| **Day 17 --- refactron verify as Standalone Command**                 |
|                                                                       |
| -   **refactron verify \<file\> \--against \<original\>** ---         |
|     standalone command that runs all 3 checks independently           |
|                                                                       |
| -   Output format:                                                    |
|                                                                       |
|     -   ✅ Syntax check (12ms)                                        |
|                                                                       |
|     -   ✅ Import integrity (8ms)                                     |
|                                                                       |
|     -   ✅ Tests passed (ran 4 test files in 6.2s)                    |
|                                                                       |
|     -   Safe to apply. Confidence: 94.1% \| Total: 6.3s               |
|                                                                       |
| -   This command works in CI on any PR that touches Python files ---  |
|     independent of autofix                                            |
|                                                                       |
| -   This is the CI/CD integration story for the MVP --- document it   |
|     prominently                                                       |
|                                                                       |
| **Days 18--19 --- Real-World Repo Testing**                           |
|                                                                       |
| **Run Refactron on 5 real open-source Python repos. Do not ship until |
| all 5 pass without crashes.**                                         |
|                                                                       |
|                                                                       |
|  ---------------- ----------------------- --------------------------- |
|   **Repository**   **What to Test For**    **Success Criteria**       |
|                                                                       |
|   **Flask (80k     Analyzer coverage,      *Zero crashes. Skip        |
|   lines)**         TaintAnalyzer skip      warnings displayed         |
|                    rate, import graph      correctly.*                |
|                    accuracy                                           |
|                                                                       |
|   **Requests (15k  Output quality, issue   *Clean output in under 30  |
|   lines)**         grouping, summary       seconds.*                  |
|                    accuracy                                           |
|                                                                       |
|   **FastAPI (40k   Autofix dry-run, diff   *Diff is readable and      |
|   lines)**         quality, no false       correct.*                  |
|                    positives on modern                                |
|                    syntax                                             |
|                                                                       |
|   **Httpx (25k     Verification Engine on  *Blocks 0 good transforms. |
|   lines)**         real autofix candidates Allows safe ones.*         |
|                                                                       |
|   **Black (30k     Self-hosting edge case  *Zero crashes. Ironic but  |
|   lines)**         --- a formatter         critical.*                 |
|                    formatting itself                                  |
|                                                                       |
|  ---------------- ----------------------- --------------------------- |
|                                                                       |
| **Day 20 --- CLAUDE.md Update + v1.1.0 Pre-Release**                  |
|                                                                       |
| -   Update CLAUDE.md to include refactron/verification/ directory,    |
|     VerificationResult contract, and the inviolable safety rule       |
|                                                                       |
| -   Add verification module architecture to CLAUDE.md architecture    |
|     section --- Claude Code needs this context                        |
|                                                                       |
| -   Create CHANGELOG.md entry for v1.1.0 listing all new capabilities |
|                                                                       |
| -   Publish v1.1.0-beta.1 to TestPyPI --- verify install and basic    |
|     commands work on a clean machine                                  |
|                                                                       |
| -   Do NOT publish to PyPI yet --- Week 5 validation gates the real   |
|     release                                                           |
|                                                                       |
| +------------------------------------------------------------------+  |
| | **✅ Week 4 Gate --- Must Pass Before Week 5 Starts**            |  |
| |                                                                  |  |
| | Fresh pip install on a real Python project → useful output in    |  |
| | under 2 minutes.                                                 |  |
| |                                                                  |  |
| | refactron verify works as a standalone CI command.               |  |
| |                                                                  |  |
| | Zero crashes on all 5 real-world repos.                          |  |
| |                                                                  |  |
| | All error messages are human-readable --- no stack traces        |  |
| | visible to end users.                                            |  |
| |                                                                  |  |
| | v1.1.0-beta.1 installs cleanly from TestPyPI.                    |  |
| +------------------------------------------------------------------+  |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
| **PHASE 4** Real User Validation → Ship v1.1.0 Week 5 · Days 21--25   |
+-----------------------------------------------------------------------+
| **Goal: 3 of 5 external developers say \"I would use this on my       |
| production codebase\"**                                               |
|                                                                       |
| **You are not building this week.** You are watching real developers  |
| use what you built and deciding whether it is ready to ship.          |
|                                                                       |
| **Days 21--22 --- Find and Brief 5 Target Developers**                |
|                                                                       |
| -   Profile: senior engineers at scale-ups, 50k--500k line Python     |
|     codebases, real technical debt pain                               |
|                                                                       |
| -   Not colleagues who will be polite. Developers who will tell you   |
|     when something is broken.                                         |
|                                                                       |
| -   Brief: \"Install it, run it on your codebase, tell me what        |
|     happens. I will not explain anything.\"                           |
|                                                                       |
| -   Give zero guidance --- the points of confusion they hit are your  |
|     next release priority list                                        |
|                                                                       |
| -   Record sessions (with permission) or pair silently --- do not     |
|     explain, do not interrupt                                         |
|                                                                       |
| **Days 23--24 --- Observe, Document, Decide**                         |
|                                                                       |
| -   Watch where they get confused --- that is a UX bug, not user      |
|     error                                                             |
|                                                                       |
| -   Watch what they try first --- that tells you what your mental     |
|     model of the product is wrong about                               |
|                                                                       |
| -   Watch what makes them say something positive --- that is your     |
|     actual value proposition                                          |
|                                                                       |
| -   Document every piece of feedback verbatim --- this becomes the    |
|     v1.2.0 backlog                                                    |
|                                                                       |
| -   Track: crashes found, confusing outputs, missing docs, unexpected |
|     behaviors                                                         |
|                                                                       |
| **Day 25 --- The Go/No-Go Decision**                                  |
|                                                                       |
|   --------------------------------- --------------------------------- |
|   **SHIP --- Conditions Met**       **DO NOT SHIP --- Fix First**     |
|                                                                       |
|   3+ of 5 say \"I would use this on Fewer than 3 of 5 validate ---    |
|   my real codebase\"                find the blocking problem         |
|                                                                       |
|   Zero P0 crashes during any user   Any crash that a user hits during |
|   session                           testing                           |
|                                                                       |
|   Verification Engine blocks at     Verification engine is bypassed   |
|   least 1 real bad transform        or throws                         |
|                                                                       |
|   At least 1 developer asks \"When  Users finish sessions confused    |
|   can my team get this?\"           about what the tool does          |
|   --------------------------------- --------------------------------- |
|                                                                       |
| -   **If SHIP:** Publish v1.1.0 to PyPI. Post to Hacker News Show HN. |
|     Write the launch blog post on refactron.dev/blog.                 |
|                                                                       |
| -   **If NO GO:** Do not publish. Fix the single most blocking issue  |
|     found. Retest with 2 of the same developers. Re-evaluate.         |
|                                                                       |
| +------------------------------------------------------------------+  |
| | **✅ Week 5 Gate --- The MVP Is Shipped**                        |  |
| |                                                                  |  |
| | 3 of 5 external developers validated the core value proposition. |  |
| |                                                                  |  |
| | Zero P0 crashes during all user sessions.                        |  |
| |                                                                  |  |
| | v1.1.0 published to PyPI.                                        |  |
| |                                                                  |  |
| | Launch blog post live on refactron.dev/blog.                     |  |
| |                                                                  |  |
| | Show HN post submitted.                                          |  |
| +------------------------------------------------------------------+  |
+-----------------------------------------------------------------------+

**Part 5 --- How Refactron Is Different**

**5.1 The Only Column That Matters**

Every competitor has at least one of these columns. No competitor has
all five. The Verifies column is empty across the entire market. That is
the product.

  ---------------- ----------- ----------- -------------- ------------ -----------
  **Tool**         **Finds**   **Fixes**   **Verifies**   **Learns**   **Offline
                                                                       CI**

  Claude Code      \~          ✅          ❌             ❌           ❌

  Cursor           \~          ✅          ❌             \~           ❌

  GitHub Copilot   \~          \~          ❌             \~           ❌

  Amazon Q         ✅          \~          ❌             ❌           \~

  SonarQube        ✅          ❌          ❌             ❌           ✅

  Semgrep          ✅          ❌          ❌             ❌           ✅

  Bandit           \~          ❌          ❌             ❌           ✅

  **Refactron      ✅          ✅          **✅**         ❌           ✅
  v1.1.0**
  ---------------- ----------- ----------- -------------- ------------ -----------

+-----------------------------------------------------------------------+
| **💡 The Research-Backed Positioning Numbers**                        |
|                                                                       |
| AI tools break code in 63% of refactoring attempts --- CodeScene,     |
| 100,000+ samples                                                      |
|                                                                       |
| No single SAST tool detects more than 40% of real-world Python        |
| vulnerabilities --- ICSE 2026                                         |
|                                                                       |
| Developers with AI tools were 19% slower, but believed they were 20%  |
| faster --- METR 2025 RCT                                              |
|                                                                       |
| Semgrep\'s experimental autofix produces incorrect code in 3.6% of    |
| cases --- no verification step                                        |
|                                                                       |
| These numbers are your entire marketing message. Lead with them.      |
+-----------------------------------------------------------------------+

**5.2 Claude Code Is Not a Competitor**

This distinction matters for positioning and should be part of every
conversation about Refactron.

  ----------------------------------- -----------------------------------
  **Claude Code**                     **Refactron**

  You prompt it conversationally      Runs automatically --- no prompting

  You review every diff manually      Verification Engine proves it is
                                      safe

  Non-deterministic --- different     Deterministic --- identical result
  result each run                     every time

  Requires Anthropic API to function  Fully offline --- air-gapped CI
                                      ready

  No static analysis engine           Deep taint, data flow, CFG analysis

  No CI/CD quality gates              Native PR blocking on CRITICAL
                                      issues

  A smart colleague you pair with     A safety inspector that runs
                                      autonomously

  ***These are not competing. Claude  ***A developer can use both in the
  Code = active pairing. Refactron =  same workflow without conflict.***
  autonomous safety enforcement.***
  ----------------------------------- -----------------------------------

**Part 6 --- Post-MVP Backlog (Priority Order)**

Do not start any of these until the Week 5 gate is cleared and real user
feedback is in hand. The order below is based on what the research says
has the most impact, not on what is most interesting to build.

  -------- -------------------- ------------------------- ----------------------- ----------
  **\#**   **Feature**          **Why This Order**        **Success Signal**      **v**

  **1**    **Harden             Skip rate data from real  *Skip rate drops below  **v1.2**
           TaintAnalyzer +      users will show which AST 5% on real repos*
           DataFlowAnalyzer**   patterns to fix. Build
                                this based on evidence,
                                not guesses.

  **2**    **Semantic           Deepest verification      *Blocks 1 transform     **v1.2**
           Equivalence Check    layer. Only viable after  that test gate missed*
           (Check 4)**          Test Suite Gate is proven
                                solid across real
                                codebases.

  **3**    **LLM Suggestions    Intelligence on top of    *80%+ suggestion        **v1.3**
           (Groq, hardened)**   proven safety. Never the  approval rate in user
                                other way. LLM = advisor, testing*
                                never operator.

  **4**    **RAG Context        Reduces LLM               *Measurable suggestion  **v1.3**
           (ChromaDB,           hallucinations 60--80%.   quality improvement*
           project-aware)**     Only valuable once the
                                LLM layer is stable.

  **5**    **SARIF Output**     Single biggest enterprise *Passes GitHub Advanced **v1.4**
                                CI/CD unlock. GitHub      Security validation*
                                Advanced Security, Azure
                                DevOps, GitLab all
                                consume it.

  **6**    **Pattern Learning   Needs real user           *Measurable noise       **v1.5**
           Engine**             accept/reject data to     reduction after 30
                                produce anything. Useless days*
                                before you have users.

  **7**    **refactron init     Quality of life ---       *Time-to-first-output   **v1.5**
           Command**            auto-detect framework,    under 90 seconds*
                                build RAG index, write
                                config. Not needed to
                                prove core value.

  **8**    **Type Consistency   Optional verification     *Zero new false         **v1.5**
           (mypy, Check 5)**    layer. Configurable,      positives on real
                                default off. Catches type codebases*
                                regressions from
                                refactors.

  **9**    **VSCode Extension** Only after CLI is         *500+ installs in first **v2.0**
                                perfect. Extension is CLI month*
                                under the hood. Builds on
                                all the above.
  -------- -------------------- ------------------------- ----------------------- ----------

**Part 7 --- Non-Negotiables and Today\'s Actions**

**7.1 Five Rules That Cannot Be Broken**

These are architectural invariants and process rules. If any of them
slip, the MVP is not a safety-first product.

  ------- --------------------------- ----------------------------------------
  **1**   **Original file never       All checks run against a temp file. The
          touched during              real file is written ONLY after
          verification**              safe_to_apply is True. This must be
                                      enforced in code --- no way to bypass
                                      it.

  **2**   **Verification blocks 100%  One bad transform slipping through
          of known-bad transforms**   destroys trust permanently. 99% accuracy
                                      is not acceptable for a safety-first
                                      tool. Validate against fixtures every CI
                                      run.

  **3**   **Zero crashes on all 5     Run on Flask, Requests, FastAPI, Httpx,
          real-world repos before     and Black before v1.1.0 goes to PyPI.
          shipping**                  Fix every crash found. No exceptions.

  **4**   **\--dry-run shows diff     Developers must see what will change
          before any write**          before anything changes. No way to
                                      bypass this. Autofix without dry-run is
                                      not an MVP feature.

  **5**   **External user validation  3 of 5 external developers must
          before PyPI publish**       validate. Internal testing is not
                                      validation. The people who built it
                                      cannot be the only people who test it.
  ------- --------------------------- ----------------------------------------

**7.2 The Three Actions for Today --- Right Now**

  ------- ------------------------------ -------------------------------------------------
  **1**   **Run: refactron analyze       Point the library at itself. Every crash is Day 1
          refactron/**                   work. This is the fastest way to find what needs
                                         fixing before building anything new.

  **2**   **Create result.py and lock    Define every field in the dataclass. Lock it.
          VerificationResult**           Every module downstream depends on this contract.
                                         Build nothing else until it is locked.

  **3**   **Write                        tests/verification/test_blocks_bad_transform.py
          test_blocks_bad_transform.py   must fail today. That failing test is the target.
          --- make it fail**             Weeks 2--3 are about making it pass.
  ------- ------------------------------ -------------------------------------------------

+-----------------------------------------------------------------------+
| The entire MVP is one sentence:                                       |
|                                                                       |
| **\"I ran Refactron on my production codebase.**                      |
|                                                                       |
| ***It found real issues, fixed the safe ones, and proved --- with     |
| evidence --- that nothing would break.\"***                           |
|                                                                       |
| Build only what is required for a developer to say that sentence.     |
|                                                                       |
| Repo connect is done. The plan is final. Open the terminal.           |
+-----------------------------------------------------------------------+
