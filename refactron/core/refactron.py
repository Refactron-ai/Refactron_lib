"""Main Refactron class - the entry point for all operations."""

import logging
import os
import time
from pathlib import Path
from typing import List, Optional, Tuple, Union

from refactron.analysis.cfg.builder import CFGBuilder
from refactron.analysis.taint import TaintAnalyzer
from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.analyzers.code_smell_analyzer import CodeSmellAnalyzer
from refactron.analyzers.complexity_analyzer import ComplexityAnalyzer
from refactron.analyzers.dead_code_analyzer import DeadCodeAnalyzer
from refactron.analyzers.dependency_analyzer import DependencyAnalyzer
from refactron.analyzers.performance_analyzer import PerformanceAnalyzer
from refactron.analyzers.security_analyzer import SecurityAnalyzer
from refactron.analyzers.type_hint_analyzer import TypeHintAnalyzer
from refactron.core.analysis_result import AnalysisResult, FileAnalysisError
from refactron.core.cache import ASTCache
from refactron.core.config import RefactronConfig
from refactron.core.exceptions import AnalysisError, RefactoringError
from refactron.core.incremental import IncrementalAnalysisTracker
from refactron.core.logging_config import setup_logging
from refactron.core.memory_profiler import MemoryProfiler
from refactron.core.metrics import get_metrics_collector
from refactron.core.models import AnalysisSkipWarning, FileMetrics, RefactoringOperation
from refactron.core.parallel import ParallelProcessor
from refactron.core.prometheus_metrics import start_metrics_server
from refactron.core.refactor_result import RefactorResult
from refactron.core.telemetry import get_telemetry_collector
from refactron.patterns import PatternFingerprinter, PatternStorage
from refactron.refactorers.add_docstring_refactorer import AddDocstringRefactorer
from refactron.refactorers.base_refactorer import BaseRefactorer
from refactron.refactorers.extract_method_refactorer import ExtractMethodRefactorer
from refactron.refactorers.magic_number_refactorer import MagicNumberRefactorer
from refactron.refactorers.reduce_parameters_refactorer import ReduceParametersRefactorer
from refactron.refactorers.simplify_conditionals_refactorer import SimplifyConditionalsRefactorer

# Configure logging
logger = logging.getLogger(__name__)


class Refactron:
    """
    Main Refactron class for code analysis and refactoring.

    Example:
        >>> refactron = Refactron()
        >>> result = refactron.analyze("mycode.py")
        >>> print(result.report())
    """

    def __init__(self, config: Optional[RefactronConfig] = None):
        """
        Initialize Refactron.

        Args:
            config: Configuration object. If None, uses default config.
        """
        self.config = config or RefactronConfig.default()
        self.analyzers: List[BaseAnalyzer] = []
        self.refactorers: List[BaseRefactorer] = []

        # Initialize structured logging using the configured settings
        self.structured_logger = setup_logging(
            level=self.config.log_level,
            log_file=self.config.log_file,
            log_format=self.config.log_format,
            max_bytes=self.config.log_max_bytes,
            backup_count=self.config.log_backup_count,
            enable_console=self.config.enable_console_logging,
            enable_file=self.config.enable_file_logging,
        )

        # Initialize metrics collection
        if self.config.enable_metrics:
            self.metrics_collector = get_metrics_collector()
        else:
            self.metrics_collector = None

        # Initialize telemetry
        if self.config.enable_telemetry:
            self.telemetry_collector = get_telemetry_collector(enabled=True)
        else:
            self.telemetry_collector = None

        # Start Prometheus metrics server if enabled
        if self.config.enable_prometheus:
            try:
                start_metrics_server(
                    host=self.config.prometheus_host,
                    port=self.config.prometheus_port,
                )
                logger.info(
                    f"Prometheus metrics server started on "
                    f"{self.config.prometheus_host}:{self.config.prometheus_port}"
                )
            except Exception as e:
                logger.warning(f"Failed to start Prometheus metrics server: {e}")

        # Initialize performance optimization components
        self.ast_cache = ASTCache(
            cache_dir=self.config.ast_cache_dir,
            enabled=self.config.enable_ast_cache,
            max_cache_size_mb=self.config.max_ast_cache_size_mb,
            cleanup_threshold_percent=self.config.cache_cleanup_threshold_percent,
        )

        self.incremental_tracker = IncrementalAnalysisTracker(
            state_file=self.config.incremental_state_file,
            enabled=self.config.enable_incremental_analysis,
        )

        self.parallel_processor = ParallelProcessor(
            max_workers=self.config.max_parallel_workers,
            use_processes=self.config.use_multiprocessing,
            enabled=self.config.enable_parallel_processing,
        )

        self.memory_profiler = MemoryProfiler(
            enabled=self.config.enable_memory_profiling,
            pressure_threshold_percent=self.config.memory_pressure_threshold_percent,
            pressure_threshold_available_mb=self.config.memory_pressure_threshold_available_mb,
        )

        # Initialize pattern learning components (if enabled)
        self.pattern_storage = None
        self.pattern_fingerprinter = None
        self.pattern_learner = None
        self.pattern_matcher = None
        self.pattern_ranker = None

        if self.config.enable_pattern_learning:
            try:
                # Initialize storage with custom directory if provided
                storage_dir = self.config.pattern_storage_dir
                self.pattern_storage = PatternStorage(storage_dir=storage_dir)
                self.pattern_fingerprinter = PatternFingerprinter()

                from refactron.patterns.learner import PatternLearner
                from refactron.patterns.matcher import PatternMatcher
                from refactron.patterns.ranker import RefactoringRanker

                # Initialize learner only if learning is enabled
                if self.config.pattern_learning_enabled:
                    self.pattern_learner = PatternLearner(
                        storage=self.pattern_storage,
                        fingerprinter=self.pattern_fingerprinter,
                    )

                # Matcher is only needed when ranking is enabled
                if self.config.pattern_ranking_enabled:
                    self.pattern_matcher = PatternMatcher(storage=self.pattern_storage)
                    # Initialize ranker only if ranking is enabled
                    self.pattern_ranker = RefactoringRanker(
                        storage=self.pattern_storage,
                        matcher=self.pattern_matcher,
                        fingerprinter=self.pattern_fingerprinter,
                    )

                logger.debug("Pattern learning system initialized successfully")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize pattern learning system: {e}. "
                    "Pattern learning features will be disabled."
                )
                # Ensure all components are None on failure
                self.pattern_storage = None
                self.pattern_fingerprinter = None
                self.pattern_learner = None
                self.pattern_matcher = None
                self.pattern_ranker = None
        else:
            logger.debug("Pattern learning is disabled in configuration")

        self._initialize_analyzers()
        self._initialize_refactorers()

    def _initialize_analyzers(self) -> None:
        """Initialize all enabled analyzers."""
        if "complexity" in self.config.enabled_analyzers:
            self.analyzers.append(ComplexityAnalyzer(self.config))

        if "code_smells" in self.config.enabled_analyzers:
            self.analyzers.append(CodeSmellAnalyzer(self.config))

        if "security" in self.config.enabled_analyzers:
            self.analyzers.append(SecurityAnalyzer(self.config))

        if "dependency" in self.config.enabled_analyzers:
            self.analyzers.append(DependencyAnalyzer(self.config))

        if "dead_code" in self.config.enabled_analyzers:
            self.analyzers.append(DeadCodeAnalyzer(self.config))

        if "type_hints" in self.config.enabled_analyzers:
            self.analyzers.append(TypeHintAnalyzer(self.config))

        if "performance" in self.config.enabled_analyzers:
            self.analyzers.append(PerformanceAnalyzer(self.config))

    def _initialize_refactorers(self) -> None:
        """Initialize all enabled refactorers."""
        if "extract_method" in self.config.enabled_refactorers:
            self.refactorers.append(ExtractMethodRefactorer(self.config))

        if "extract_constant" in self.config.enabled_refactorers:
            self.refactorers.append(MagicNumberRefactorer(self.config))

        if "simplify_conditionals" in self.config.enabled_refactorers:
            self.refactorers.append(SimplifyConditionalsRefactorer(self.config))

        if "reduce_parameters" in self.config.enabled_refactorers:
            self.refactorers.append(ReduceParametersRefactorer(self.config))

        if "add_docstring" in self.config.enabled_refactorers:
            self.refactorers.append(AddDocstringRefactorer(self.config))

    def analyze(self, target: Union[str, Path]) -> AnalysisResult:
        """
        Analyze a file or directory.

        Args:
            target: Path to file or directory to analyze

        Returns:
            AnalysisResult containing all detected issues and any errors encountered

        Note:
            This method implements graceful degradation - if individual files fail
            to analyze, they are logged and skipped, allowing analysis to continue
            on remaining files.
        """
        # Start metrics collection
        if self.metrics_collector:
            self.metrics_collector.start_analysis()

        # Start memory profiling
        if self.memory_profiler.enabled:
            self.memory_profiler.snapshot("analysis_start")

        target_path = Path(target)

        if not target_path.exists():
            raise FileNotFoundError(f"Target not found: {target}")

        if target_path.is_file():
            files = [target_path]
        else:
            files = self.get_python_files(target_path)

        # Apply incremental analysis filtering
        if self.incremental_tracker.enabled:
            original_count = len(files)
            files = self.incremental_tracker.get_changed_files(files)
            logger.info(f"Incremental analysis: analyzing {len(files)} of {original_count} files")

        result = AnalysisResult(total_files=len(files))

        # Use parallel processing if enabled and multiple files
        if self.parallel_processor.enabled and len(files) > 1:
            logger.info(
                f"Using parallel processing with {self.parallel_processor.max_workers} workers"
            )

            # Create a wrapper function for parallel processing
            def process_file_wrapper(
                file_path: Path,
            ) -> Tuple[Optional[FileMetrics], Optional[FileAnalysisError]]:
                try:
                    file_metrics, skip_warn = self._analyze_file(file_path)
                    if skip_warn is not None:
                        result.semantic_skip_warnings.append(skip_warn)

                    # Update incremental tracker
                    if self.incremental_tracker.enabled:
                        self.incremental_tracker.update_file_state(file_path)

                    return file_metrics, None
                except AnalysisError as e:
                    logger.debug(f"Failed to analyze {file_path}: {e}")
                    error = FileAnalysisError(
                        file_path=file_path,
                        error_message=str(e),
                        error_type=e.__class__.__name__,
                        recovery_suggestion=e.recovery_suggestion,
                    )
                    return None, error
                except Exception as e:
                    logger.error(f"Unexpected error analyzing {file_path}: {e}", exc_info=True)
                    error = FileAnalysisError(
                        file_path=file_path,
                        error_message=str(e),
                        error_type=e.__class__.__name__,
                        recovery_suggestion="Check the file for syntax errors or encoding issues",
                    )
                    return None, error

            # Process files in parallel
            file_metrics_list, error_list = self.parallel_processor.process_files(
                files,
                process_file_wrapper,
            )

            result.file_metrics.extend(file_metrics_list)
            result.failed_files.extend(error_list)
            result.total_issues = sum(fm.issue_count for fm in file_metrics_list)
        else:
            # Sequential processing
            for file_path in files:
                try:
                    file_metrics, skip_warn = self._analyze_file(file_path)
                    result.file_metrics.append(file_metrics)
                    result.total_issues += file_metrics.issue_count
                    if skip_warn is not None:
                        result.semantic_skip_warnings.append(skip_warn)

                    # Update incremental tracker
                    if self.incremental_tracker.enabled:
                        self.incremental_tracker.update_file_state(file_path)
                except AnalysisError as e:
                    logger.debug(f"Failed to analyze {file_path}: {e}")
                    result.failed_files.append(
                        FileAnalysisError(
                            file_path=file_path,
                            error_message=str(e),
                            error_type=e.__class__.__name__,
                            recovery_suggestion=e.recovery_suggestion,
                        )
                    )
                except Exception as e:
                    logger.error(f"Unexpected error analyzing {file_path}: {e}", exc_info=True)
                    recovery_msg = "Check the file for syntax errors or encoding issues"
                    result.failed_files.append(
                        FileAnalysisError(
                            file_path=file_path,
                            error_message=str(e),
                            error_type=e.__class__.__name__,
                            recovery_suggestion=recovery_msg,
                        )
                    )

        # Compute semantic skip summary if skip_rate > 10%
        total_analyzed = len(result.file_metrics)
        skipped_count = len(result.semantic_skip_warnings)
        if total_analyzed > 0 and skipped_count / total_analyzed > 0.10:
            result.semantic_skip_summary = (
                f"⚠ Semantic analysis (taint) was skipped for {skipped_count} of "
                f"{total_analyzed} files ({skipped_count / total_analyzed * 100:.0f}%). "
                "Check logs for details. Common causes: unsupported syntax or very large files."
            )
            logger.warning(result.semantic_skip_summary)

        # Save incremental state
        if self.incremental_tracker.enabled:
            self.incremental_tracker.save()

        # End metrics collection
        if self.metrics_collector:
            self.metrics_collector.end_analysis()

            # Record telemetry event
            if self.telemetry_collector:
                analyzer_names = [a.__class__.__name__ for a in self.analyzers]
                summary = self.metrics_collector.get_analysis_summary()
                self.telemetry_collector.record_analysis_completed(
                    files_analyzed=summary.get("total_files_analyzed", 0),
                    total_time_ms=summary.get("total_analysis_time_ms", 0),
                    issues_found=summary.get("total_issues_found", 0),
                    analyzers_used=analyzer_names,
                )

        # End memory profiling
        if self.memory_profiler.enabled:
            self.memory_profiler.snapshot("analysis_end")
            diff = self.memory_profiler.compare("analysis_start", "analysis_end")
            if diff:
                logger.info(f"Analysis memory usage: +{diff['rss_mb_diff']:.2f} MB")

        return result

    def _run_semantic_analysis(
        self, file_path: Path, source_code: str
    ) -> Tuple[list, Optional["AnalysisSkipWarning"]]:
        """Run TaintAnalyzer on *source_code* with full exception isolation.

        Returns:
            (vulnerabilities, None) on success, or ([], AnalysisSkipWarning) on any failure.
            The caller is guaranteed this method never raises.
        """
        try:
            cfg = CFGBuilder().build_from_source(source_code)
            ta = TaintAnalyzer(cfg)
            vulnerabilities = ta.analyze()
            return vulnerabilities, None
        except Exception as e:
            short_reason = f"{type(e).__name__}: {e}"
            logger.debug("Semantic analysis (taint) skipped for %s: %s", file_path, short_reason)
            return [], AnalysisSkipWarning(
                file_path=file_path,
                analyzer_name="taint",
                reason=short_reason,
            )

    def _analyze_file(
        self, file_path: Path
    ) -> Tuple["FileMetrics", Optional["AnalysisSkipWarning"]]:
        """Analyze a single file.

        Args:
            file_path: Path to file to analyze

        Returns:
            FileMetrics with analysis results

        Raises:
            AnalysisError: If file cannot be analyzed
        """
        # Track analysis time
        start_time = time.time()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
        except UnicodeDecodeError as e:
            # Record failed analysis metric
            if self.metrics_collector and self.config.metrics_detailed:
                analysis_time_ms = (time.time() - start_time) * 1000
                self.metrics_collector.record_file_analysis(
                    file_path=str(file_path),
                    analysis_time_ms=analysis_time_ms,
                    lines_of_code=0,
                    issues_found=0,
                    analyzers_run=[],
                    success=False,
                    error_message="Encoding error",
                )
            raise AnalysisError(
                f"Failed to read file due to encoding error: {e}",
                file_path=file_path,
            ) from e
        except (IOError, OSError) as e:
            # Record failed analysis metric
            if self.metrics_collector and self.config.metrics_detailed:
                analysis_time_ms = (time.time() - start_time) * 1000
                self.metrics_collector.record_file_analysis(
                    file_path=str(file_path),
                    analysis_time_ms=analysis_time_ms,
                    lines_of_code=0,
                    issues_found=0,
                    analyzers_run=[],
                    success=False,
                    error_message="I/O error",
                )
            raise AnalysisError(
                f"Failed to read file: {e}",
                file_path=file_path,
            ) from e

        # Initialize basic metrics
        try:
            lines = source_code.split("\n")
            loc = len([line for line in lines if line.strip() and not line.strip().startswith("#")])
            comment_lines = len([line for line in lines if line.strip().startswith("#")])
            blank_lines = len([line for line in lines if not line.strip()])

            metrics = FileMetrics(
                file_path=file_path,
                lines_of_code=loc,
                comment_lines=comment_lines,
                blank_lines=blank_lines,
                complexity=0.0,
                maintainability_index=100.0,
                functions=0,
                classes=0,
            )
        except Exception as e:
            raise AnalysisError(
                f"Failed to compute basic metrics: {e}",
                file_path=file_path,
            ) from e

        # Track which analyzers run
        analyzers_run = []

        # Run all analyzers with individual error handling
        for analyzer in self.analyzers:
            try:
                issues = analyzer.analyze(file_path, source_code)
                metrics.issues.extend(issues)
                analyzers_run.append(analyzer.name)

                # Track analyzer hits for each issue
                # Note: Issues are expected to have a 'category' attribute for type tracking
                if self.metrics_collector:
                    for issue in issues:
                        issue_type = getattr(issue, "category", "unknown")
                        self.metrics_collector.record_analyzer_hit(
                            analyzer_name=analyzer.name, issue_type=issue_type
                        )
            except Exception as e:
                # Log analyzer failure but continue with other analyzers
                # Use debug level for expected errors, warning for unexpected
                if isinstance(e, AnalysisError):
                    logger.debug(f"Analyzer {analyzer.name} failed for {file_path}: {e}")
                else:
                    logger.warning(
                        f"Analyzer {analyzer.name} failed for {file_path}: {e}",
                        exc_info=True,
                    )
                # Don't raise - allow other analyzers to run

        # Run semantic analysis (TaintAnalyzer) with full exception isolation
        _, skip_warning = self._run_semantic_analysis(file_path, source_code)

        # Record file analysis metrics
        if self.metrics_collector and self.config.metrics_detailed:
            analysis_time_ms = (time.time() - start_time) * 1000
            self.metrics_collector.record_file_analysis(
                file_path=str(file_path),
                analysis_time_ms=analysis_time_ms,
                lines_of_code=loc,
                issues_found=len(metrics.issues),
                analyzers_run=analyzers_run,
                success=True,
            )

        return metrics, skip_warning

    def refactor(
        self,
        target: Union[str, Path],
        preview: bool = True,
        operation_types: Optional[List[str]] = None,
    ) -> RefactorResult:
        """
        Refactor a file or directory.

        Args:
            target: Path to file or directory to refactor
            preview: If True, show changes without applying them
            operation_types: Specific refactoring operations to apply (None = all)

        Returns:
            RefactorResult containing all proposed operations

        Note:
            This method implements graceful degradation - if individual files fail
            to refactor, they are logged and skipped, allowing refactoring to continue
            on remaining files.
        """
        target_path = Path(target)

        if not target_path.exists():
            raise FileNotFoundError(f"Target not found: {target}")

        if target_path.is_file():
            files = [target_path]
        else:
            files = self.get_python_files(target_path)

        result = RefactorResult(preview_mode=preview)

        for file_path in files:
            try:
                operations = self._refactor_file(file_path, operation_types)
                result.operations.extend(operations)
            except RefactoringError as e:
                # Log the error and continue with other files
                logger.warning(f"Failed to refactor {file_path}: {e}")
                # Store error in result if needed (RefactorResult could be extended)
            except Exception as e:
                # Catch unexpected errors to ensure refactoring continues
                logger.error(f"Unexpected error refactoring {file_path}: {e}", exc_info=True)

        # Rank operations if pattern ranking is enabled and ranker is available
        if result.operations and self.config.pattern_ranking_enabled and self.pattern_ranker:
            try:
                # Detect project root for project-specific ranking
                project_path = None
                if files:
                    try:
                        project_path = self.detect_project_root(files[0])
                    except Exception as e:
                        logger.debug(f"Failed to detect project root for ranking: {e}")

                # Rank operations
                ranked_operations = self.pattern_ranker.rank_operations(
                    result.operations, project_path=project_path
                )

                # Update operations list with ranked order
                result.operations = [op for op, _ in ranked_operations]

                # Store ranking scores in operation metadata
                for operation, score in ranked_operations:
                    operation.metadata["ranking_score"] = score

            except Exception as e:
                # If ranking fails, continue with unranked operations
                logger.debug(f"Failed to rank operations: {e}")

        return result

    def _refactor_file(
        self,
        file_path: Path,
        operation_types: Optional[List[str]] = None,
    ) -> List:
        """Refactor a single file.

        Args:
            file_path: Path to file to refactor
            operation_types: Specific operation types to apply

        Returns:
            List of refactoring operations

        Raises:
            RefactoringError: If file cannot be refactored
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
        except UnicodeDecodeError as e:
            raise RefactoringError(
                f"Failed to read file due to encoding error: {e}",
                file_path=file_path,
            ) from e
        except (IOError, OSError) as e:
            raise RefactoringError(
                f"Failed to read file: {e}",
                file_path=file_path,
            ) from e

        operations = []

        # Run all refactorers with individual error handling
        for refactorer in self.refactorers:
            if operation_types and refactorer.operation_type not in operation_types:
                continue

            try:
                ops = refactorer.refactor(file_path, source_code)

                # Fingerprint code patterns for each operation
                if self.pattern_fingerprinter:
                    for op in ops:
                        try:
                            # Fingerprint the old code pattern
                            pattern_hash = self.pattern_fingerprinter.fingerprint_code(op.old_code)
                            # Store pattern hash in operation metadata
                            op.metadata["code_pattern_hash"] = pattern_hash
                        except Exception as e:
                            logger.debug(f"Failed to fingerprint code pattern: {e}")

                operations.extend(ops)
            except Exception as e:
                # Log refactorer failure but continue with other refactorers
                logger.warning(
                    f"Refactorer {refactorer.__class__.__name__} failed for {file_path}: {e}",
                    exc_info=True,
                )
                # Don't raise - allow other refactorers to run

        return operations

    def get_python_files(self, directory: Path) -> List[Path]:
        """Get all Python files in a directory, respecting exclude patterns."""
        python_files = []

        for root, dirs, files in os.walk(directory):
            root_path = Path(root)

            # Check if this directory should be excluded
            if self._should_exclude(root_path):
                dirs.clear()  # Don't descend into this directory
                continue

            for file in files:
                if file.endswith(".py"):
                    file_path = root_path / file
                    if not self._should_exclude(file_path):
                        python_files.append(file_path)

        return python_files

    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded based on patterns."""
        path_str = str(path)

        for pattern in self.config.exclude_patterns:
            # Simple pattern matching
            pattern_clean = pattern.replace("**/", "").replace("/**", "")
            if pattern_clean in path_str:
                return True

        return False

    def get_performance_stats(self) -> dict:
        """
        Get performance statistics from all optimization components.

        Returns:
            Dictionary containing performance statistics.
        """
        return {
            "ast_cache": self.ast_cache.get_stats(),
            "incremental_analysis": self.incremental_tracker.get_stats(),
            "parallel_processing": self.parallel_processor.get_config(),
            "memory_profiler": self.memory_profiler.get_stats(),
        }

    def record_feedback(
        self,
        operation_id: str,
        action: str,
        reason: Optional[str] = None,
        operation: Optional[RefactoringOperation] = None,
    ) -> None:
        """
        Record developer feedback on a refactoring suggestion.

        Args:
            operation_id: Unique identifier for the refactoring operation
            action: Feedback action - "accepted", "rejected", or "ignored"
            reason: Optional reason for the feedback
            operation: Optional RefactoringOperation object (used to extract metadata)

        Note:
            If pattern storage is not initialized, this method will silently fail.
        """
        if (
            not self.config.enable_pattern_learning
            or not self.pattern_storage
            or action not in ("accepted", "rejected", "ignored")
        ):
            return

        try:
            from refactron.patterns.models import RefactoringFeedback

            # Extract metadata from operation if provided
            code_pattern_hash = None
            project_path = None
            operation_type = "unknown"
            file_path = Path(".")

            # Prepare metadata for operation reconstruction if needed
            operation_metadata = {}
            if operation:
                operation_type = operation.operation_type
                file_path = operation.file_path
                code_pattern_hash = operation.metadata.get("code_pattern_hash")

                # Store operation details in metadata for later reconstruction
                # (useful if learning fails initially and needs to be retried)
                operation_metadata = {
                    "old_code": operation.old_code,
                    "new_code": operation.new_code,
                    "line_number": operation.line_number,
                    "description": operation.description,
                    "risk_score": operation.risk_score,
                }

                # Try to detect project root
                try:
                    project_path = self.detect_project_root(file_path)
                except Exception as e:
                    logger.debug(
                        "Failed to detect project root for %s: %s",
                        file_path,
                        e,
                    )

            # Create feedback record
            feedback = RefactoringFeedback.create(
                operation_id=operation_id,
                operation_type=operation_type,
                file_path=file_path,
                action=action,
                code_pattern_hash=code_pattern_hash,
                project_path=project_path,
                reason=reason,
                metadata=operation_metadata,
            )

            # Save feedback
            self.pattern_storage.save_feedback(feedback)
            logger.debug(f"Recorded feedback for operation {operation_id}: {action}")

            # Automatically learn from feedback if learning is enabled and operation provided
            if operation and self.config.pattern_learning_enabled and self.pattern_learner:
                try:
                    pattern_id = self.pattern_learner.learn_from_feedback(operation, feedback)
                    if pattern_id:
                        logger.debug(
                            f"Learned pattern {pattern_id} from feedback for "
                            f"operation {operation_id}"
                        )
                except Exception as e:
                    # Don't fail feedback recording if learning fails
                    logger.debug(f"Learning from feedback failed (non-critical): {e}")

        except Exception as e:
            logger.warning(f"Failed to record feedback: {e}", exc_info=True)

    def detect_project_root(self, file_path: Path) -> Path:
        """
        Detect project root by looking for common markers in parent directories.

        The search walks up the directory tree from the file's parent directory,
        checking for common project markers up to a fixed maximum depth.

        Args:
            file_path: Path to a file in the project.

        Returns:
            The path to the project root if any of the known markers are found
            within the search depth limit, or the file's parent directory if no
            markers are detected.
        """
        current = file_path.parent.resolve()

        # Common project markers
        markers = [
            ".git",
            "setup.py",
            "pyproject.toml",
            "setup.cfg",
            ".refactron",
            ".refactron.yaml",
        ]

        for _ in range(10):  # Limit search depth
            for marker in markers:
                if (current / marker).exists():
                    return current
            if current.parent == current:  # Reached filesystem root
                break
            current = current.parent

        return file_path.parent  # Fallback to file's parent directory

    def clear_caches(self) -> None:
        """Clear all performance-related caches."""
        logger.info("Clearing all caches...")
        self.ast_cache.clear()
        self.incremental_tracker.clear()
        self.memory_profiler.clear_snapshots()
        logger.info("Caches cleared successfully")
