"""Tests for the Refactron pipeline module."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from refactron.core.pipeline import RefactronPipeline
from refactron.core.config import RefactronConfig

def test_pipeline_loads_project_config():
    """Test that RefactronPipeline loads configuration from the project root."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root_path = Path(temp_dir)
        
        config_path = root_path / ".refactron.yaml"
        config_path.write_text("max_function_complexity: 99\nenable_metrics: false\n")
        
        target_file = root_path / "dummy.py"
        target_file.write_text("def foo():\n    pass\n")
        
        pipeline = RefactronPipeline(project_root=root_path)
        
        with patch("refactron.core.pipeline.Refactron") as MockRefactron:
            instance = MockRefactron.return_value
            instance.analyze.return_value = "mock_result"
            
            result = pipeline.analyze(target_file)
            
            assert result == "mock_result"
            args, _ = MockRefactron.call_args
            config_passed = args[0]
            
            assert isinstance(config_passed, RefactronConfig)
            assert config_passed.max_function_complexity == 99
            assert config_passed.enable_metrics is False
            assert config_passed.enable_incremental_analysis is False

def test_pipeline_incremental_override():
    """Test that RefactronPipeline can override the incremental setting."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root_path = Path(temp_dir)
        
        target_file = root_path / "dummy.py"
        target_file.write_text("def foo():\n    pass\n")
        
        pipeline = RefactronPipeline(project_root=root_path)
        
        with patch("refactron.core.pipeline.Refactron") as MockRefactron:
            pipeline.analyze(target_file, use_incremental=True)
            
            args, _ = MockRefactron.call_args
            config_passed = args[0]
            assert config_passed.enable_incremental_analysis is True
