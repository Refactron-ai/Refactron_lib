"""Pipeline orchestration for automated and session-based flows."""

from pathlib import Path
from typing import Optional, Union

from refactron.core.config import RefactronConfig
from refactron.core.refactron import Refactron
from refactron.core.analysis_result import AnalysisResult

class RefactronPipeline:
    """Automated pipeline execution for session-based and CI/CD flows."""

    def __init__(self, project_root: Optional[Union[str, Path]] = None, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize the pipeline.

        Args:
            project_root: Optional root directory of the project.
            config_path: Optional explicit configuration path.
        """
        self.project_root = Path(project_root) if project_root else None
        self.config_path = Path(config_path) if config_path else None

    def analyze(self, target: Union[str, Path], use_incremental: bool = False) -> AnalysisResult:
        """
        Run analysis as part of a pipeline flow.

        Pipeline-only overrides:
        - `enable_incremental_analysis` is forced to `use_incremental` (default False) to guarantee
          a fully fresh, reproducible analysis in CI/CD or pipeline environments unless explicitly enabled.

        Args:
            target: Path to file or directory to analyze.
            use_incremental: Optional override to enable incremental analysis (off by default for pipelines).

        Returns:
            AnalysisResult containing issues and metrics.
        """
        target_path = Path(target)
        
        # 1. Resolve config the same way as CLI
        if self.config_path and self.config_path.exists():
            config = RefactronConfig.from_file(self.config_path)
        else:
            if not self.project_root:
                try:
                    self.project_root = Refactron().detect_project_root(target_path)
                except Exception:
                    self.project_root = target_path if target_path.is_dir() else target_path.parent
                    
            yaml_path = self.project_root / ".refactron.yaml"
            if yaml_path.exists():
                config = RefactronConfig.from_file(yaml_path)
            else:
                config = RefactronConfig.default()

        # 2. Allow explicit overrides
        # In pipeline mode, incremental analysis is off by default for consistency
        config.enable_incremental_analysis = use_incremental

        refactron = Refactron(config)
        return refactron.analyze(target)
